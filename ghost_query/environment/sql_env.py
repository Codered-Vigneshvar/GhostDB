import time
import json
from typing import Dict, Any, Tuple
from openenv.core.env_server import Environment

from ghost_query.environment.engine import DBEngine
from ghost_query.environment.grader import verify_integrity
from ghost_query.environment.logger import TrajectoryLogger
from ghost_query.models import SQLAction, SQLObservation, SQLState

class SQLEnv(Environment):
    SUPPORTS_CONCURRENT_SESSIONS = False

    def __init__(self):
        super().__init__()
        self.engine = None
        self.baseline_latency_ms = None
        self.baseline_query = ""
        self.current_task_name = ""
        self._current_state = SQLState()
        self.baseline_df = None
        self.steps = 0
        self.logger = TrajectoryLogger()

    @property
    def state(self) -> Any:
        return self._current_state

    def reset(self) -> Tuple[SQLObservation, SQLState, Dict[str, Any]]:
        if self.engine is not None:
            self.engine.close()
        
        self.engine = DBEngine()
        
        self.current_task_name = "default_session"
        self.baseline_query = ""
        self.baseline_latency_ms = 0.0
        self.baseline_df = None
        
        obs = SQLObservation(
            latency_ms=0.0,
            query_plan_json="{}",
            error_msg=None
        )
        obs.original_sql = ""
        obs.baseline_latency = 0.0
        obs.is_valid = None
        
        state = SQLState(
            current_latency_ms=0.0,
            baseline_latency_ms=0.0,
            step_count=0
        )
        self.steps = 0
        
        return obs, state, {"task": self.current_task_name}

    def step(self, action: SQLAction) -> Tuple[SQLObservation, float, bool, bool, Dict[str, Any]]:
        self.steps += 1
        reward = 0.0
        is_valid = False
        terminated = False
        info = {}

        obs, latency = self._execute_query(action.sql_query)
        
        if obs.error_msg:
            obs.is_valid = False
            reward = -1.0
            terminated = True
            info = {"error": "Syntax Error", "reason": obs.error_msg}
        else:
            try:
                baseline_df = self.baseline_df
                optimized_df = self.engine.execute(action.sql_query).df()
                
                is_valid = verify_integrity(baseline_df, optimized_df)
                obs.is_valid = is_valid
                
                if is_valid:
                    if self.baseline_latency_ms > 0:
                        reward = (self.baseline_latency_ms - obs.latency_ms) / self.baseline_latency_ms
                    else:
                        reward = 0.0
                    reward -= (self.steps * 0.05)
                    info = {"status": "Success", "reason": "Optimized with exact bit-fidelity."}
                else:
                    reward = -1.0
                    info = {"error": "Data Corruption", "reason": "Hash mismatch on result set."}
                
                terminated = True # Internal task termination
                
            except Exception as e:
                obs.is_valid = False
                reward = -1.0
                terminated = True
                info = {"error": "Data Corruption", "reason": f"Execution mismatch: {str(e)}"}

        if self.steps >= 5:
            terminated = True

        self.logger.log_step(self.current_task_name, self.steps, obs, action, reward)
        return obs, reward, terminated, False, info

    def _execute_query(self, query: str) -> Tuple[SQLObservation, float]:
        try:
            # Strip simple SQL comments to prevent EXPLAIN from choking on them
            clean_query = "\n".join([line for line in query.split("\n") if not line.strip().startswith("--")])
            
            plan_res = self.engine.execute(f"EXPLAIN {clean_query}").fetchall()
            plan_json = str(plan_res)
            
            start_time = time.time()
            self.engine.execute(query)
            latency_ms = (time.time() - start_time) * 1000.0
            
            obs = SQLObservation(
                latency_ms=latency_ms,
                query_plan_json=plan_json,
                error_msg=None
            )
            return obs, latency_ms
        except Exception as e:
            obs = SQLObservation(
                latency_ms=0.0,
                query_plan_json="{}",
                error_msg=str(e)
            )
            return obs, 0.0
