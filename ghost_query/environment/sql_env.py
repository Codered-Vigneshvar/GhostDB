import time
import json
from typing import Dict, Any, Tuple
from openenv.core.env_server import Environment

from ghost_query.environment.engine import DBEngine
from ghost_query.environment.grader import verify_integrity
from ghost_query.models import SQLAction, SQLObservation, SQLState

class SQLEnv(Environment):
    def __init__(self):
        super().__init__()
        self.engine = None
        self.baseline_latency_ms = None
        self.baseline_query = ""

    def reset(self) -> Tuple[SQLObservation, SQLState, Dict[str, Any]]:
        if self.engine is not None:
            self.engine.close()
        
        self.engine = DBEngine(':memory:')
        self.engine.seed_data(row_count=100000)
        
        self.baseline_query = """
        SELECT 
            s1.region_id, 
            COUNT(DISTINCT s1.transaction_id) as total_txns, 
            SUM(s1.amount) as total_sales
        FROM Sales s1
        INNER JOIN Sales s2 ON s1.status = s2.status
        WHERE s1.status LIKE '%COMPLETED%' OR s1.status LIKE '%completed%'
        GROUP BY s1.region_id
        """
        
        obs, latency = self._execute_query(self.baseline_query)
        self.baseline_latency_ms = latency
        
        state = SQLState(
            current_latency_ms=self.baseline_latency_ms,
            baseline_latency_ms=self.baseline_latency_ms,
            step_count=0
        )
        
        return obs, state, {}

    def step(self, action: SQLAction) -> Tuple[SQLObservation, float, bool, bool, Dict[str, Any]]:
        obs, latency = self._execute_query(action.sql_query)
        
        if obs.error_msg:
            return obs, -1.0, True, False, {"error": "Syntax Error", "reason": obs.error_msg}
            
        try:
            baseline_df = self.engine.execute(self.baseline_query).df()
            optimized_df = self.engine.execute(action.sql_query).df()
            
            is_valid = verify_integrity(baseline_df, optimized_df)
            
            if is_valid:
                if self.baseline_latency_ms > 0:
                    reward = (self.baseline_latency_ms - obs.latency_ms) / self.baseline_latency_ms
                else:
                    reward = 0.0
                info = {"status": "Success", "reason": "Optimized with exact bit-fidelity."}
            else:
                reward = -1.0
                info = {"error": "Data Corruption", "reason": "Hash mistmatch on result set. Invalid optimizations."}
            
            return obs, reward, True, False, info
            
        except Exception as e:
            return obs, -1.0, True, False, {"error": "Data Corruption", "reason": f"Execution mismatch: {str(e)}"}

    def _execute_query(self, query: str) -> Tuple[SQLObservation, float]:
        try:
            plan_res = self.engine.execute(f"EXPLAIN FORMAT JSON {query}").fetchone()
            plan_json = str(plan_res[0])
            
            start_time = time.time()
            self.engine.execute(query)
            latency_ms = (time.time() - start_time) * 1000.0
            
            obs = SQLObservation(
                latency_ms=latency_ms,
                bytes_scanned=0,
                query_plan_json=plan_json,
                error_msg=None
            )
            return obs, latency_ms
        except Exception as e:
            obs = SQLObservation(
                latency_ms=0.0,
                bytes_scanned=0,
                query_plan_json="{}",
                error_msg=str(e)
            )
            return obs, 0.0
