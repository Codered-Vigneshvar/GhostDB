import os
import json
from typing import Any, Dict

class TrajectoryLogger:
    def __init__(self, log_path: str = None):
        if log_path is None:
            # Default to AgentCode/trajectory.json relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "agent", "AgentCode")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            self.log_path = os.path.join(log_dir, "trajectory.json")
        else:
            self.log_path = log_path

    def log_step(self, task_id: str, step: int, observation: Any, action: Any, reward: float):
        """
        Appends a flat [State, Action, Reward] triplet to the trajectory JSON.
        """
        entry = {
            "task_id": task_id,
            "step": step,
            "observation": {
                "original_sql": getattr(observation, "original_sql", ""),
                "baseline_latency": getattr(observation, "baseline_latency", 0),
                "latency_ms": getattr(observation, "latency_ms", 0),
                "query_plan": getattr(observation, "query_plan_json", "{}")
            },
            "action": getattr(action, "sql_query", str(action)),
            "reward": reward
        }

        data = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, IOError):
                data = []

        data.append(entry)

        with open(self.log_path, "w") as f:
            json.dump(data, f, indent=2)
