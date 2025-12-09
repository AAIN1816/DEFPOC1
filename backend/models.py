from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# -------- Pydantic Models -------- #

class DQRuleRequest(BaseModel):
    databaseType: str
    schemaName: str
    tableName: str
    columnName: List[str]       # multiple columns
    dqRule: List[str]           # rule names selected by user


class DQRuleResponse(BaseModel):
    run_id: str
    databaseType: str
    schemaName: str
    tableName: str
    columnName: List[str]
    dqRule: List[str]
    status: str
    result_path: Optional[str]
    created_at: datetime
