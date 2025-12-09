from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.db import Base, engine
from backend.models_sql import DQRunEntry      # <-- SQLAlchemy model
import json


# ---------------------------------------------------------
#   GET DB SESSION
# ---------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------
#   CREATE RUN ENTRY (INSERT)
# ---------------------------------------------------------
def create_run_entry(databaseType, schemaName, tableName, columnList, rule_id_list):
    db = SessionLocal()

    entry = DQRunEntry(
        databaseType=databaseType,
        schemaName=schemaName,
        tableName=tableName,
        columnName=json.dumps(columnList),
        dqRule=json.dumps(rule_id_list),
        status="PENDING"
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    db.close()
    return entry


# ---------------------------------------------------------
#   UPDATE RESULT (AFTER JOB TRIGGER)
# ---------------------------------------------------------
def update_entry_result(run_id, status, result_path):
    db = SessionLocal()

    entry = db.query(DQRunEntry).filter(DQRunEntry.run_id == run_id).first()
    if entry:
        entry.status = status
        entry.result_path = result_path
        db.commit()

    db.close()
    return entry


# ---------------------------------------------------------
#   GET LAST RUN ENTRY
# ---------------------------------------------------------
def get_last_run():
    db = SessionLocal()
    entry = (
        db.query(DQRunEntry)
        .order_by(DQRunEntry.created_at.desc())
        .first()
    )
    db.close()
    return entry


# ---------------------------------------------------------
#   GET ENTRY BY RUN ID
# ---------------------------------------------------------
def get_entry_by_run_id(run_id: str):
    db = SessionLocal()
    entry = db.query(DQRunEntry).filter(DQRunEntry.run_id == run_id).first()
    db.close()
    return entry
