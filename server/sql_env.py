import sys
import os
import time
import json
import duckdb
from typing import Dict, Any, Tuple

from openenv.core.env_server import Environment

from scripts.seed_data import generate_messy_sales_data
from models import SQLAction, SQLObservation, SQLState
from grader import verify_integrity

class SQLEnv(Environment):
    def __init__(self):
        super().__init__()
        self.conn = None
        self.baseline_latency_ms = None
        self.baseline_query = ""

    def reset(self) -> Tuple[SQLObservation, SQLState, Dict[str, Any]]:
        if self.conn is not None:
            self.conn.close()
        
        # Initialize memory DB
        self.conn = duckdb.connect(':memory:')
        
        # Seed 100k row Sales data
        generate_messy_sales_data(self.conn, row_count=100000)
        
        # The unoptimized baseline query (creates deliberate Cartesian inefficiencies / Full scans)
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
            # Science Standard: Every Penalty MUST include a clear reason in 'info'
            return obs, -1.0, True, False, {"error": "Syntax Error", "reason": obs.error_msg}
            
        try:
            # Grader Logic: Evaluate bit-fidelity
            baseline_df = self.conn.execute(self.baseline_query).df()
            optimized_df = self.conn.execute(action.sql_query).df()
            
            is_valid = verify_integrity(baseline_df, optimized_df)
            
            if is_valid:
                # RL Reward Standard: R = (T_baseline - T_optimized) / T_baseline
                # Capped or scaled correctly. We make sure not to div-zero.
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
            # Request JSON formatted query plan
            # DuckDB PRAGMA explain_output='all' can get detailed, but 'EXPLAIN FORMAT JSON' is standard
            plan_res = self.conn.execute(f"EXPLAIN FORMAT JSON {query}").fetchone()
            plan_json = str(plan_res[0])
            
            # Record execution Latency
            start_time = time.time()
            self.conn.execute(query)
            latency_ms = (time.time() - start_time) * 1000.0
            
            obs = SQLObservation(
                latency_ms=latency_ms,
                bytes_scanned=0, # Extrapolated in a real detailed wrapper
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
