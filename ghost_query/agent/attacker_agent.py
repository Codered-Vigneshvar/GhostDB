import os
import json
import uuid
import random
from typing import Optional, Dict, Any

from ghost_query.environment.baseline_runner import BaselineRunner
from ghost_query.environment.project_summary import ProjectSummaryBuilder
from ghost_query.agent.attacker_planner import AttackerPlanner

class AttackerAgent:
    def __init__(self, engine):
        """
        Accepts the DBEngine instance so it can mutate the active memory data.
        """
        self.engine = engine
        self.planner = AttackerPlanner()
        self.baseline_runner = BaselineRunner(engine)
        self.summary_builder = ProjectSummaryBuilder()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.metadata_dir = os.path.join(os.path.dirname(current_dir), "metadata", "attack_truth")
        os.makedirs(self.metadata_dir, exist_ok=True)
        
        # Map attack types to methods
        self.attack_map = {
            "null_injection": self._attack_null_injection,
            "timestamp_shift": self._attack_timestamp_shift,
            "duplicate_injection": self._attack_duplicate_injection,
            "join_explosion": self._attack_join_explosion,
            "skewed_data": self._attack_skewed_data
        }

    def generate_attack(self, seed: Optional[int] = None, round_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Asks the LLM to plan an attack based on the baseline, then executes it.
        """
        if seed is not None:
            random.seed(seed)
            
        # 1. Get Project Summary (NO RESET)
        baseline_data = self.baseline_runner.run_baseline()
        summary = self.summary_builder.build_summary(baseline_data)
        
        # 2. Plan Attack via LLM
        plan = self.planner.plan_attack(summary)
        attack_type = plan.get("attack_type", "null_injection")
        
        # 3. Execute Attack
        attack_func = self.attack_map.get(attack_type, self._attack_null_injection)
        attack_details = attack_func()
        
        # 4. Merge Planner Insights into Metadata
        attack_id = uuid.uuid4().hex[:8]
        round_id = round_id if round_id else attack_id
        
        attack_details.update({
            "reason": plan.get("reason", "No reason provided"),
            "expected_impact": plan.get("expected_impact", "No impact provided"),
            "severity": plan.get("severity", "medium"),
            "round_id": round_id
        })
        
        self._log_attack_metadata(attack_details)
        
        print(f"[ATTACK] Mode: LLM-Driven")
        print(f"[ATTACK] Type: {attack_details['attack_type']}")
        print(f"[ATTACK] Target: {attack_details['target_table']}")
        print(f"[ATTACK] Reason: {attack_details['reason']}")
        print(f"[ATTACK] Completed")
        
        return {
            "round_id": round_id,
            "attack_type": attack_details["attack_type"],
            "target_table": attack_details["target_table"],
            "summary": attack_details["description"],
            "reason": attack_details["reason"]
        }

    def _log_attack_metadata(self, attack_details: Dict[str, Any]):
        round_id = attack_details["round_id"]
        filepath = os.path.join(self.metadata_dir, f"round_{round_id}.json")
        with open(filepath, 'w') as f:
            json.dump(attack_details, f, indent=4)

    # --- ATTACK PROCEDURES ---
    
    def _attack_null_injection(self) -> Dict[str, Any]:
        table = "sales"
        column = "amount"
        self.engine.execute(f"UPDATE {table} SET {column} = NULL WHERE random() < 0.05")
        self._persist_change(table)
        return {
            "attack_type": "null_injection",
            "target_table": table,
            "target_column": column,
            "description": f"Injected NULLs into {table}.{column}.",
            "expected_fix": f"UPDATE {table} SET {column} = 0 WHERE {column} IS NULL"
        }

    def _persist_change(self, table: str):
        """Persists the in-memory DuckDB table back to its workspace parquet file."""
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        target_path = os.path.join(root_dir, "workspace", "data", f"{table}.parquet")
        self.engine.execute(f"COPY {table} TO '{target_path}' (FORMAT PARQUET)")
        print(f"[ATTACK] Persisted corruption to {target_path}")

    def _attack_timestamp_shift(self) -> Dict[str, Any]:
        table = "sales"
        column = "sale_time_str"
        query = f"UPDATE {table} SET {column} = (CAST({column} AS TIMESTAMP) + INTERVAL 1 DAY)::VARCHAR WHERE random() < 0.05"
        self.engine.execute(query)
        self._persist_change(table)
        return {
            "attack_type": "timestamp_shift",
            "target_table": table,
            "target_column": column,
            "description": f"Shifted {table}.{column} by +1 day.",
            "expected_fix": "Table restore or reverse shift."
        }

    def _attack_duplicate_injection(self) -> Dict[str, Any]:
        table = "market_trends"
        self.engine.execute(f"INSERT INTO {table} SELECT * FROM {table} USING SAMPLE 10 PERCENT")
        self._persist_change(table)
        return {
            "attack_type": "duplicate_injection",
            "target_table": table,
            "target_column": "ALL",
            "description": f"Duplicated 10% of rows in {table}.",
            "expected_fix": f"CREATE OR REPLACE TABLE {table} AS SELECT DISTINCT * FROM {table}"
        }

    def _attack_join_explosion(self) -> Dict[str, Any]:
        table = "customers"
        column = "cust_id"
        self.engine.execute(f"INSERT INTO {table} SELECT * FROM {table} LIMIT 1000")
        self._persist_change(table)
        return {
            "attack_type": "join_explosion",
            "target_table": table,
            "target_column": column,
            "description": f"Injected duplicate customer IDs to trigger join explosion.",
            "expected_fix": "Remove duplicate keys from dimension table."
        }

    def _attack_skewed_data(self) -> Dict[str, Any]:
        table = "sales"
        column = "cust_id"
        self.engine.execute(f"UPDATE {table} SET {column} = 999999 WHERE random() < 0.2")
        self._persist_change(table)
        return {
            "attack_type": "skewed_data",
            "target_table": table,
            "target_column": column,
            "description": f"Created heavy data skew on {table}.{column}.",
            "expected_fix": "Rebalance partitions or filter skewed keys."
        }
