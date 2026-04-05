import os
import time
from typing import Dict, Any
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine

class BaselineRunner:
    def __init__(self, engine: DBEngine = None):
        self.engine = engine if engine else DBEngine()
        self.reset_manager = ResetManager()

    def run_baseline(self) -> Dict[str, Any]:
        """
        Executes a simple query pipeline and captures metrics.
        Assumes workspace is already reset.
        """
        start_time = time.time()
        
        metrics = {
            "runtime_ms": 0,
            "tables": {}
        }
        
        tables_to_check = ["sales", "market_trends", "customers"]
        
        try:
            for table in tables_to_check:
                # Basic row count
                row_count = self.engine.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                table_metrics = {"row_count": row_count}

                # BROAD HEALTH CHECK: Iterate through all columns
                columns = self.engine.execute(f"DESCRIBE {table}").fetchall()
                col_stats = {}
                for col in columns:
                    col_name = col[0]
                    # NULLs
                    nulls = self.engine.execute(f"SELECT COUNT(*) FROM {table} WHERE \"{col_name}\" IS NULL").fetchone()[0]
                    # Cardinality
                    card = self.engine.execute(f"SELECT COUNT(DISTINCT \"{col_name}\") FROM {table}").fetchone()[0]
                    
                    col_stats[col_name] = {
                        "null_count": nulls,
                        "cardinality": card
                    }
                
                table_metrics["columns"] = col_stats
                # Legacy keys for backward compatibility with summary builder
                if "cust_id" in col_stats:
                    table_metrics["cust_id_cardinality"] = col_stats["cust_id"]["cardinality"]
                if "amount" in col_stats:
                    table_metrics["null_count"] = col_stats["amount"]["null_count"]

                metrics["tables"][table] = table_metrics
                
            end_time = time.time()
            runtime_ms = int((end_time - start_time) * 1000)
            metrics["runtime_ms"] = runtime_ms
            
            print(f"[BASELINE] runtime={runtime_ms} ms")
            
            return metrics
            
        except Exception as e:
            print(f"[BASELINE] Error during execution: {e}")
            return metrics

if __name__ == "__main__":
    runner = BaselineRunner()
    print(runner.run_baseline())
