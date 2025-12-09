from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from backend.db import Base
import uuid

def generate_run_id():
    return f"run_{uuid.uuid4().hex[:12]}"

class DQRunEntry(Base):
    __tablename__ = "dq_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(String, unique=True, default=generate_run_id)
    databaseType = Column(String)
    schemaName = Column(String)
    tableName = Column(String)
    columnName = Column(Text)      # JSON list of columns
    dqRule = Column(Text)          # JSON rule IDs
    status = Column(String, default="PENDING")
    result_path = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
