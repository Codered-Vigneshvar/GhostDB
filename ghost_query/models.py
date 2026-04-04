import json
from typing import Dict, Any, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None

class SQLAction(BaseModel):
    sql_query: str = Field(..., description="The optimized SQL query intended purely to return the same exact result set as the original unoptimized query but faster.")

class SQLObservation(BaseModel):
    original_sql: Optional[str] = Field(None, description="The messy SQL string (available on reset).")
    baseline_latency: Optional[float] = Field(None, description="Baseline latency in ms (available on reset).")
    latency_ms: Optional[float] = Field(None, description="Execution time in milliseconds of the new query run.")
    query_plan_json: str = Field(..., description="The query execution plan (JSON/String format depending on DB).")
    error_msg: Optional[str] = Field(None, description="Detailed error message if the query failed, otherwise None.")
    is_valid: Optional[bool] = Field(None, description="Whether the result set perfectly matches the baseline result set.")

class SQLState(BaseModel):
    current_latency_ms: Optional[float] = None
    baseline_latency_ms: Optional[float] = None
    step_count: int = 0

