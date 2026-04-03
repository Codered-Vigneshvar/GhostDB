import json
from typing import Dict, Any, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback or dummy class for environments strictly missing pydantic
    class BaseModel:
        pass
    def Field(*args, **kwargs):
        return None

class SQLAction(BaseModel):
    sql_query: str = Field(..., description="The optimized SQL query intended purely to return the same exact result set as the original unoptimized query but faster.")

class SQLObservation(BaseModel):
    latency_ms: float = Field(..., description="Execution time in milliseconds of the query run.")
    bytes_scanned: int = Field(..., description="Estimated or actual bytes scanned during execution.")
    query_plan_json: str = Field(..., description="The query execution plan in JSON string format.")
    error_msg: Optional[str] = Field(None, description="Detailed error message if the query failed, otherwise None.")

class SQLState(BaseModel):
    # State tracking if necessary for full RL tracking over time
    current_latency_ms: Optional[float] = None
    baseline_latency_ms: Optional[float] = None
    step_count: int = 0
