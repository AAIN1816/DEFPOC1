from databricks import sql
import requests
import json

from backend.config import (
    DATABRICKS_HOST,
    DATABRICKS_HTTP_PATH,
    DATABRICKS_TOKEN,
    DATABRICKS_JOB_ID,
)


# ============================================================
# FETCH COLUMNS FROM UNITY CATALOG
# ============================================================

def fetch_columns_from_unity_catalog(catalog: str, schema: str, table: str):
    """
    Uses Databricks SQL Warehouse to fetch column names from UC.
    """
    try:
        if not (DATABRICKS_HOST and DATABRICKS_HTTP_PATH and DATABRICKS_TOKEN):
            raise Exception("Databricks SQL connection variables missing.")

        conn = sql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
        )
        cursor = conn.cursor()

        query = f"""
            SELECT column_name
            FROM {catalog}.information_schema.columns
            WHERE table_schema = '{schema}'
              AND table_name = '{table}'
            ORDER BY ordinal_position
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        return [r[0] for r in rows]

    except Exception as e:
        print("❌ Databricks Column Fetch Error:", str(e))
        raise



# ============================================================
# TRIGGER DATABRICKS JOB
# ============================================================

def trigger_databricks_job(payload: dict):
    """
    Calls Databricks Jobs API using /jobs/run-now
    """
    try:
        if not (DATABRICKS_HOST and DATABRICKS_TOKEN and DATABRICKS_JOB_ID):
            return {"status": "DATABRICKS_NOT_CONFIGURED"}

        url = f"{DATABRICKS_HOST}/api/2.1/jobs/run-now"
        headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}"}

        body = {
            "job_id": int(DATABRICKS_JOB_ID),
            "notebook_params": payload,
        }

        response = requests.post(url, json=body, headers=headers)
        return response.json()

    except Exception as e:
        print("❌ Databricks Job Trigger Error:", str(e))
        return {"status": "ERROR", "message": str(e)}



# ============================================================
# INSERT CONFIG METADATA INTO UC TABLE
# ============================================================

def insert_config_metadata_uc(config_id, rule_ids, catalog, schema, table, columns, created_by):
    """
    Inserts a configuration record into UC metadata table:
      dqf_catalog.dqf_metadata.dq_config_metadata

    Columns supported:
      CONFIG_ID, RULE_ID, CATALOG_NAME, SCHEMA_NAME, TABLE_NAME, COLUMN_NAME, CREATED_BY, CREATED_TS
    """
    try:
        conn = sql.connect(
            server_hostname=DATABRICKS_HOST,
            http_path=DATABRICKS_HTTP_PATH,
            access_token=DATABRICKS_TOKEN,
        )
        cursor = conn.cursor()

        rule_str = ", ".join(rule_ids)          # e.g. "DQ001, DQ004"
        column_str = ", ".join(columns)         # e.g. "col1, col2"

        insert_query = f"""
            INSERT INTO dqf_catalog.dqf_metadata.dq_config_metadata
            (CONFIG_ID, RULE_ID, CATALOG_NAME, SCHEMA_NAME, TABLE_NAME, COLUMN_NAME, CREATED_BY, CREATED_TS)
            VALUES
            ('{config_id}', '{rule_str}', '{catalog}', '{schema}', '{table}', '{column_str}', '{created_by}', current_timestamp())
        """

        cursor.execute(insert_query)

        cursor.close()
        conn.close()

        print(f"✔ UC metadata inserted for CONFIG_ID={config_id}")
        return True

    except Exception as e:
        print("❌ Error inserting into UC metadata table:", str(e))
        return False



# ============================================================
# FETCH MOST RECENT CONFIG FROM UC TABLE
# ============================================================

def fetch_last_config_from_uc():
    """
    Fetches the latest inserted configuration record from UC
    using CREATED_TS descending.

    Output:
      {
        "config_id": "...",
        "rule_id": "DQ001, DQ004",
        "catalog": "dqf_catalog",
        "schema": "dqf_metadata",
        "table": "employees",
        "columns": "age, salary",
        "created_by": "API_RUN",
        "created_ts": <timestamp>,
      }
    """
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

        if not row:
            print("⚠ No UC config rows found.")
            return None

        return {
            "config_id": row[0],
            "rule_id": row[1],
            "catalog": row[2],
            "schema": row[3],
            "table": row[4],
            "columns": row[5],
            "created_by": row[6],
            "created_ts": row[7],
        }

    except Exception as e:
        print("❌ Error fetching last UC config:", str(e))
        return None
