import json
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from databricks import sql

from backend.models import DQRuleRequest, DQRuleResponse
from backend.services.databricks_service import (
    fetch_columns_from_unity_catalog,
    trigger_databricks_job,
    insert_config_metadata_uc,
)
from backend.services.adls_service import download_blob_stream
from backend.config import (
    DATABRICKS_HOST,
    DATABRICKS_HTTP_PATH,
    DATABRICKS_TOKEN,
)

# =====================================================
# DQ RULE DEFINITIONS
# =====================================================

DQ_RULE_NAME_TO_ID = {
    "Null Check": "DQ001",
    "Numeric Check": "DQ002",
    "Range Check": "DQ003",
    "Duplicate Check": "DQ004",
    "Reference Check": "DQ005",
}

# reverse mapping for reprocess response
DQ_RULE_ID_TO_NAME = {v: k for k, v in DQ_RULE_NAME_TO_ID.items()}

DQ_RULE_MASTER = {
    "DQ001": {
        "rule_name": "NULL_CHECK",
        "rule_description": "Checks for NULL values",
        "rule_expression": "SELECT COUNT(*) FROM {table} WHERE {col} IS NULL",
        "rule_type": "Completeness",
    },
    "DQ002": {
        "rule_name": "NUMERIC_CHECK",
        "rule_description": "Ensures only numeric values",
        "rule_expression": "SELECT COUNT(*) FROM {table} WHERE {col} NOT REGEXP '^[0-9]+$'",
        "rule_type": "Validity",
    },
    "DQ003": {
        "rule_name": "RANGE_CHECK",
        "rule_description": "Checks min/max range",
        "rule_expression": "SELECT COUNT(*) FROM {table} WHERE {col} < {min_val} OR {col} > {max_val}",
        "rule_type": "Accuracy",
    },
    "DQ004": {
        "rule_name": "DUPLICATE_CHECK",
        "rule_description": "Checks duplicates",
        "rule_expression": "SELECT {col}, COUNT(*) FROM {table} GROUP BY {col} HAVING COUNT(*) > 1",
        "rule_type": "Uniqueness",
    },
    "DQ005": {
        "rule_name": "REFERENCE_CHECK",
        "rule_description": "Validates foreign keys",
        "rule_expression": (
            "SELECT COUNT(*) FROM {table} t "
            "LEFT JOIN ref_table r ON t.{col}=r.{ref_col} "
            "WHERE r.{ref_col} IS NULL"
        ),
        "rule_type": "Referential Integrity",
    },
}

# =====================================================
# FASTAPI APP
# =====================================================

app = FastAPI(title="DQ Framework API - Unity Catalog Metadata Only")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # you can restrict this later
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "DQ API (Unity Catalog) is running."}


# =====================================================
# HELPER: FETCH LAST CONFIG FROM UC METADATA TABLE
# =====================================================

def fetch_last_config_from_uc() -> Optional[dict]:
    """
    Reads the latest configuration row from UC table:
      dqf_catalog.dqf_metadata.dq_config_metadata

    Assumes schema like:
      CONFIG_ID, RULE_ID, CATALOG_NAME, SCHEMA_NAME, TABLE_NAME,
      COLUMN_NAME, CREATED_BY, CREATED_TS
    """
    if not (DATABRICKS_HOST and DATABRICKS_HTTP_PATH and DATABRICKS_TOKEN):
        raise Exception("Databricks SQL connection variables are missing")

    conn = None
    try:
        conn = sql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
        )
        cursor = conn.cursor()

        query = """
            SELECT
              CONFIG_ID,
              RULE_ID,
              CATALOG_NAME,
              SCHEMA_NAME,
              TABLE_NAME,
              COLUMN_NAME,
              CREATED_BY,
              CREATED_TS
            FROM dqf_catalog.dqf_metadata.dq_config_metadata
            ORDER BY CREATED_TS DESC
            LIMIT 1
        """

        cursor.execute(query)
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        conn = None

        if not row:
            return None

        return {
            "config_id": row[0],
            "rule_id": row[1],      # e.g. "DQ001, DQ004"
            "catalog": row[2],
            "schema": row[3],
            "table": row[4],
            "columns": row[5],      # e.g. "col1, col2"
            "created_by": row[6],
            "created_ts": row[7],
        }

    except Exception as e:
        if conn is not None:
            conn.close()
        print("❌ Error fetching last config from UC:", str(e))
        raise


# =====================================================
# COLUMNS ENDPOINT (UC)
# =====================================================

@app.get("/columns")
def get_columns(
    catalog: str = Query(...),
    schema: str = Query(...),
    table: str = Query(...),
):
    """
    Fetch columns using Databricks Unity Catalog via SQL Warehouse.
    """
    try:
        columns = fetch_columns_from_unity_catalog(catalog, schema, table)
        return {"columns": columns}
    except Exception as e:
        print("Column Fetch Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# CREATE & TRIGGER DQ RUN (NORMAL EXECUTION)
# =====================================================

@app.post("/dq-rule", response_model=DQRuleResponse)
def create_and_trigger(rule: DQRuleRequest):
    """
    Normal DQ execution:
      1. Validate incoming rule names
      2. Map rule names -> rule IDs
      3. Save config metadata into UC
      4. Trigger Databricks job
      5. Return run_id + status
    """
    # 1. Validate rule names and map to IDs
    rule_ids: List[str] = []
    for name in rule.dqRule:
        if name not in DQ_RULE_NAME_TO_ID:
            raise HTTPException(status_code=400, detail=f"Invalid rule: {name}")
        rule_ids.append(DQ_RULE_NAME_TO_ID[name])

    # 2. Expand full rule metadata to send to notebook
    expanded_rules = [DQ_RULE_MASTER[rid] for rid in rule_ids]

    # 3. Generate run_id and treat it as CONFIG_ID for this execution
    run_id = f"run_{uuid.uuid4().hex[:12]}"

    # 4. Store config + rule IDs into UC metadata table
    try:
        insert_ok = insert_config_metadata_uc(
            config_id=run_id,
            rule_ids=rule_ids,
            catalog=rule.databaseType,
            schema=rule.schemaName,
            table=rule.tableName,
            columns=rule.columnName,  # list[str]
            created_by="API_RUN",
        )
        if not insert_ok:
            raise Exception("insert_config_metadata_uc returned False")
    except Exception as e:
        print("❌ UC metadata insert error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to insert config metadata into UC")

    # 5. Prepare Databricks job payload
    payload = {
        "run_id": run_id,
        "config_id": run_id,
        "databaseType": rule.databaseType,
        "schemaName": rule.schemaName,
        "tableName": rule.tableName,
        "columnName": json.dumps(rule.columnName),  # list -> JSON string
        "dqRule": json.dumps(expanded_rules),
    }

    # 6. Trigger Databricks job
    dr = trigger_databricks_job(payload)

    # 7. Return API response
    return DQRuleResponse(
        run_id=run_id,
        databaseType=rule.databaseType,
        schemaName=rule.schemaName,
        tableName=rule.tableName,
        columnName=rule.columnName,
        dqRule=rule.dqRule,  # rule names as selected by UI
        status="TRIGGERED",
        result_path=json.dumps(dr),
        created_at=datetime.utcnow(),
    )


# =====================================================
# REPROCESS LAST RUN (BASED ON UC METADATA)
# =====================================================

@app.post("/reprocess-last", response_model=DQRuleResponse)
def reprocess_last():
    """
    Re-run DQ using the latest config stored in UC metadata table.
      1. Fetch last config row from UC
      2. Create a NEW run_id
      3. Insert a new metadata entry into UC for this re-run
      4. Trigger Databricks job with same catalog/schema/table/columns/rules
      5. Return new run_id
    """
    # 1. Read last config from UC
    try:
        uc = fetch_last_config_from_uc()
    except Exception as e:
        print("❌ UC fetch last config error:", e)
        raise HTTPException(status_code=500, detail="Error reading UC metadata")

    if not uc:
        raise HTTPException(status_code=404, detail="No previous UC config found to reprocess")

    # uc["rule_id"] might be "DQ001, DQ004"
    raw_rule_str = uc["rule_id"] or ""
    rule_ids: List[str] = [r.strip() for r in raw_rule_str.split(",") if r.strip()]

    if not rule_ids:
        raise HTTPException(status_code=400, detail="UC metadata has no rule IDs to reprocess")

    # Expand rules
    expanded_rules = [DQ_RULE_MASTER[rid] for rid in rule_ids]

    # uc["columns"] might be "col1, col2"
    raw_cols = uc["columns"] or ""
    columns: List[str] = [c.strip() for c in raw_cols.split(",") if c.strip()]

    if not columns:
        raise HTTPException(status_code=400, detail="UC metadata has no columns to reprocess")

    catalog = uc["catalog"]
    schema = uc["schema"]
    table = uc["table"]

    # 2. Create a NEW run_id for this reprocess execution
    new_run_id = f"run_{uuid.uuid4().hex[:12]}"

    # 3. Insert new UC metadata entry for this re-run
    try:
        insert_ok = insert_config_metadata_uc(
            config_id=new_run_id,
            rule_ids=rule_ids,
            catalog=catalog,
            schema=schema,
            table=table,
            columns=columns,
            created_by="API_REPROCESS",
        )
        if not insert_ok:
            raise Exception("insert_config_metadata_uc returned False")
    except Exception as e:
        print("❌ UC insert on reprocess error:", str(e))
        raise HTTPException(status_code=500, detail="Failed to insert reprocess config into UC")

    # 4. Prepare Databricks payload using same config but new run_id
    payload = {
        "run_id": new_run_id,
        "config_id": uc["config_id"],   # original config id if you want to track lineage
        "databaseType": catalog,
        "schemaName": schema,
        "tableName": table,
        "columnName": json.dumps(columns),
        "dqRule": json.dumps(expanded_rules),
    }

    dr = trigger_databricks_job(payload)

    # Convert rule IDs back to rule names for response
    rule_names = [DQ_RULE_ID_TO_NAME.get(rid, rid) for rid in rule_ids]

    return DQRuleResponse(
        run_id=new_run_id,
        databaseType=catalog,
        schemaName=schema,
        tableName=table,
        columnName=columns,
        dqRule=rule_names,
        status="REPROCESSED",
        result_path=json.dumps(dr),
        created_at=datetime.utcnow(),
    )


# =====================================================
# DOWNLOAD RESULTS FROM ADLS (UNCHANGED)
# =====================================================

@app.get("/download-results")
def download_results(
    run_id: str = Query(...),
    filename: str = Query("dq_results.xlsx"),
):
    """
    Stream result file from ADLS container.
    Path in storage: {run_id}/{filename}
    """
    try:
        stream = download_blob_stream(run_id, filename)
        return StreamingResponse(
            stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Result file not found")
    except Exception as e:
        print("Download error:", e)
        raise HTTPException(status_code=500, detail=str(e))
