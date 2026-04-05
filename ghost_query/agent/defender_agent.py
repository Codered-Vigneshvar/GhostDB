import os
import json
import uuid
import shutil
import difflib
import traceback
from typing import Dict, Any, List, Optional
from ghost_query.agent.defender_planner import DefenderPlanner
from ghost_query.agent.defender_context import DefenderContext
from ghost_query.environment.baseline_runner import BaselineRunner
from ghost_query.environment.project_summary import ProjectSummaryBuilder

class DefenderAgent:
    def __init__(self, engine):
        self.engine = engine
        self.planner = DefenderPlanner()
        self.baseline_runner = BaselineRunner(engine)
        self.summary_builder = ProjectSummaryBuilder()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.root_dir = os.path.dirname(current_dir)
        self.reports_dir = os.path.join(self.root_dir, "reports", "incident_reports")
        self.logs_dir = os.path.join(self.root_dir, "metadata", "round_logs")
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

    def run_defense(self, max_retries: int = 6, round_id: str = None) -> Dict[str, Any]:
        """
        Main autonomous reasoning loop.
        """
        print(f"\n[DEFENDER] Starting autonomous defense (max {max_retries} attempts)...")
        round_id = round_id if round_id else uuid.uuid4().hex[:8]
        
        # 1. Capture Initial "Broken" State & Load Baseline
        broken_metrics = self.baseline_runner.run_baseline()
        
        baseline_path = os.path.join(self.root_dir, "metadata", "baseline_metrics.json")
        baseline_ref = None
        if os.path.exists(baseline_path):
            with open(baseline_path, 'r') as f:
                baseline_ref = json.load(f)
        
        broken_summary = self.summary_builder.build_summary(broken_metrics, baseline_ref)
        
        # 2. Initialize Instrumentation
        context_mgr = DefenderContext(broken_summary)
        attempt_history = []
        previous_errors = []
        final_fix = None
        success = False
        
        # 3. Reasoning Loop
        for attempt_idx in range(max_retries):
            print(f"[DEFENDER] Attempt {attempt_idx + 1}/{max_retries}...")
            
            # A. Build Context
            context = context_mgr.build_context(broken_metrics, attempt_history, previous_errors)
            
            # B. Plan Edit
            plan = self.planner.decide_edit(context)
            if plan.get("action") == "error":
                print(f"[DEFENDER] Planner error: {plan.get('reason')}")
                previous_errors.append(plan.get("reason"))
                continue
                
            target_file = plan.get("file")
            new_code = plan.get("new_code")
            reason = plan.get("reason")
            
            # C. Safety & Paths
            if not target_file or not target_file.strip().startswith("workspace/"):
                err = f"REJECTED: Illegal file path '{target_file}'. Must be in workspace/."
                print(f"[DEFENDER] {err}")
                previous_errors.append(err)
                continue
            
            abs_target_path = os.path.join(self.root_dir, target_file)
            backup_path = abs_target_path + ".bak"
            
            # D. Syntax Validation (SQL specific)
            if target_file.endswith(".sql"):
                try:
                    # Strip possible markdown or non-SQL comments if LLM was messy
                    sql_to_test = new_code.strip()
                    self.engine.execute(f"EXPLAIN {sql_to_test}")
                except Exception as e:
                    err = f"Syntax Error in SQL: {str(e)}"
                    print(f"[DEFENDER] {err}")
                    previous_errors.append(err)
                    attempt_history.append({"file": target_file, "reason": reason, "error": err})
                    continue

            # E. Backup & Apply
            old_code = ""
            if os.path.exists(abs_target_path):
                shutil.copy(abs_target_path, backup_path)
                with open(abs_target_path, 'r') as f:
                    old_code = f.read()
            else:
                # Ensure directory exists
                os.makedirs(os.path.dirname(abs_target_path), exist_ok=True)
                with open(abs_target_path, 'w') as f: f.write("") # Create empty
                
            try:
                # Apply replacement
                with open(abs_target_path, 'w') as f:
                    f.write(new_code)
                
                # Special: If it's a SQL file, we also execute it to "patch" the memory
                if target_file.endswith(".sql"):
                    self.engine.execute(new_code)
                
                # F. Run Pipeline & Validate
                current_metrics = self.baseline_runner.run_baseline()
                
                # REFINED VALIDATION: Check for NULLs and Skew
                data_is_clean = True
                for table_name in current_metrics.get("tables", {}):
                    if table_name == "sales":
                        # Check NULLs
                        nulls = self.engine.execute("SELECT COUNT(*) FROM sales WHERE amount IS NULL").fetchone()[0]
                        # Check Skew (Customer Fan-out)
                        skew_count = self.engine.execute("SELECT COUNT(*) FROM (SELECT cust_id FROM sales GROUP BY cust_id HAVING COUNT(*) > 200000)").fetchone()[0]
                        
                        if nulls > 0 or skew_count > 0:
                            data_is_clean = False
                    
                # Detect intentional filtering to avoid false-positive anomaly flags on row drops
                plan_text = f"{reason} {new_code}".lower()
                intentional = any(k in plan_text for k in ["distinct", "delete", "where", "filter", "replace", "redistribute"])
                
                validation_summary = self.summary_builder.build_summary(current_metrics, baseline_ref, intentional_filtering=intentional)
                
                if data_is_clean and "No anomalies detected" in validation_summary:
                    print("[DEFENDER] SUCCESS: Fix validated (No NULLs, No Skew, No Anomalies).")
                    
                    # PERSIST ALL TABLES to ensure Evaluator sees the fix
                    for table in current_metrics.get("tables", {}):
                        self._persist_change(table)
                    
                    success = True
                    final_fix = {
                        "file": target_file,
                        "reason": reason,
                        "diff": self._generate_diff(old_code, new_code, target_file),
                        "metrics": current_metrics
                    }
                    attempt_history.append({"file": target_file, "reason": reason, "error": None})
                    break
                else:
                    err = "Logic improved but system still shows deviations from baseline."
                    print(f"[DEFENDER] {err}")
                    attempt_history.append({"file": target_file, "reason": reason, "error": err})
                    # Restore backup and RELOAD cache
                    if os.path.exists(backup_path):
                        shutil.copy(backup_path, abs_target_path)
                        # CRITICAL: Reload in-memory state to wipe the failed SQL
                        tbl_name = target_file.split("/")[-1].replace(".sql", "").replace(".parquet", "")
                        if tbl_name in ["sales", "market_trends", "customers"]:
                            self._reload_table(tbl_name)
            
            except Exception as e:
                err = f"Execution Error: {str(e)}"
                print(f"[DEFENDER] {err}")
                previous_errors.append(err)
                attempt_history.append({"file": target_file, "reason": reason, "error": err})
                # Restore backup and RELOAD cache
                if os.path.exists(backup_path):
                    shutil.copy(backup_path, abs_target_path)
                    # CRITICAL: Reload in-memory state to wipe the failed SQL
                    tbl_name = target_file.split("/")[-1].replace(".sql", "").replace(".parquet", "")
                    if tbl_name in ["sales", "market_trends", "customers"]:
                        self._reload_table(tbl_name)

            # G. Early stop on repeated error
            if len(previous_errors) >= 2 and previous_errors[-1] == previous_errors[-2]:
                print("[DEFENDER] STOP: Repeated error detected. Breaking loop.")
                break

        # 4. Final Verification Stats
        final_metrics = self.baseline_runner.run_baseline() if not success else final_fix["metrics"]
        
        results = {
            "round_id": round_id,
            "success": success,
            "attempts": len(attempt_history),
            "root_cause": attempt_history[0]["reason"] if attempt_history else "Unknown",
            "history": attempt_history,
            "runtime_before": broken_metrics.get("runtime_ms"),
            "runtime_after": final_metrics.get("runtime_ms"),
            "diff": final_fix["diff"] if final_fix else None
        }
        
        # 5. Logging & Reporting
        self._log_round(results)
        self._generate_incident_report(results, broken_metrics, final_metrics)
        
        return results

    def _generate_diff(self, old_code: str, new_code: str, filename: str) -> str:
        diff = difflib.unified_diff(
            old_code.splitlines(keepends=True),
            new_code.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}"
        )
        return "".join(diff)

    def _persist_change(self, table: str):
        """Persists the in-memory DuckDB table back to its workspace parquet file."""
        target_path = os.path.join(self.root_dir, "workspace", "data", f"{table}.parquet")
        self.engine.execute(f"COPY {table} TO '{target_path}' (FORMAT PARQUET)")
        print(f"[DEFENDER] Persisted fix to {target_path}")

    def _reload_table(self, table: str):
        """Reloads a table from its workspace parquet file into DuckDB memory."""
        source_path = os.path.join(self.root_dir, "workspace", "data", f"{table}.parquet")
        if os.path.exists(source_path):
            self.engine.execute(f"DROP TABLE IF EXISTS {table}")
            self.engine.execute(f"CREATE TABLE {table} AS SELECT * FROM read_parquet('{source_path}')")
            print(f"[DEFENDER] State Isolated: Reloaded {table} from disk.")

    def _log_round(self, results: Dict[str, Any]):
        path = os.path.join(self.logs_dir, f"round_{results['round_id']}.json")
        with open(path, 'w') as f:
            json.dump(results, f, indent=4)

    def _generate_incident_report(self, results: Dict[str, Any], before: Dict[str, Any], after: Dict[str, Any]):
        status = "✅ RESOLVED" if results["success"] else "❌ FAILED"
        
        # Performance Calculation
        ms_before = results.get("runtime_before", 0)
        ms_after = results.get("runtime_after", 0)
        perf_delta = ""
        if ms_before > 0:
            diff = ms_before - ms_after
            pct = (diff / ms_before) * 100
            if pct > 0:
                perf_delta = f" (Optimized by {pct:.1f}%)"
            elif pct < 0:
                perf_delta = f" (Regression of {abs(pct):.1f}%)"
        
        md = f"""# Incident Report: {results['round_id']}
        
## Summary
- **Status:** {status}
- **Retries:** {results['attempts']}
- **Performance Optimization:** {ms_before}ms -> {ms_after}ms{perf_delta}
- **Root Cause (Hypothesis):** {results['root_cause']}

## Recovery Performance
- **Runtime Before:** {ms_before} ms
- **Runtime After:** {ms_after} ms
- **Delta:** {ms_after - ms_before} ms

## Attempt History
"""
        for i, att in enumerate(results['history']):
            md += f"### Attempt {i+1}\n"
            md += f"- **File:** `{att['file']}`\n"
            md += f"- **Reasoning:** {att['reason']}\n"
            if att['error']:
                md += f"- **Error:** `{att['error']}`\n"
            else:
                md += "- **Result:** Success\n"

        if results['diff']:
            md += f"\n## Code Changes (Final Fix)\n```diff\n{results['diff']}\n```\n"

        md += f"""
## Validation Metrics Comparison
| Table | Rows (Before) | Rows (After) | Data Health (Post-Fix) |
|---|---|---|---|
"""
        before_tables = before.get("tables", {})
        after_tables = after.get("tables", {})
        for table in before_tables:
             row_b = before_tables[table].get('row_count')
             row_a = after_tables.get(table, {}).get('row_count', 'N/A')
             
             # Extract Health Tags
             health_tags = []
             metrics_a = after_tables.get(table, {})
             if metrics_a.get("null_count", 0) == 0: health_tags.append("Clean (No NULLs)")
             if "cust_id_cardinality" in metrics_a:
                 health_tags.append(f"Cardinality: {metrics_a['cust_id_cardinality']}")
             
             tag_str = ", ".join(health_tags) if health_tags else "Review Required"
             md += f"| {table} | {row_b} | {row_a} | {tag_str} |\n"

        path = os.path.join(self.reports_dir, f"round_{results['round_id']}.md")
        with open(path, 'w') as f:
            f.write(md)
