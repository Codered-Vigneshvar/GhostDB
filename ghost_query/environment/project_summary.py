from typing import Dict, Any, Optional

class ProjectSummaryBuilder:
    def build_summary(self, current_data: Dict[str, Any], baseline_ref: Optional[Dict[str, Any]] = None, intentional_filtering: bool = False) -> str:
        """
        Converts metrics into a clean, LLM-readable summary string.
        If baseline_ref is provided, it calculates deltas.
        If intentional_filtering is True, row count DROPS are not flagged as anomalies.
        """
        if not current_data or "tables" not in current_data:
            return "Project Summary: Error or no data available."
            
        summary = "Project Summary:\nTables:\n"
        
        for table, metrics in current_data["tables"].items():
            row_count = metrics.get("row_count", "unknown")
            cardinality = metrics.get("cust_id_cardinality")
            nulls = metrics.get("null_count")
            
            # Compare with baseline if available
            baseline_row_count = None
            if baseline_ref and "tables" in baseline_ref and table in baseline_ref["tables"]:
                baseline_row_count = baseline_ref["tables"][table].get("row_count")
            
            line = f"- {table} (rows: {row_count}"
            if baseline_row_count:
                diff = int(row_count) - int(baseline_row_count)
                if diff != 0:
                    line += f" [Baseline: {baseline_row_count}, Delta: {diff:+}]"
            
            if cardinality is not None:
                line += f", unique_customers: {cardinality}"
            if nulls is not None:
                line += f", nulls: {nulls}"
            line += ")\n"
            summary += line
            
        runtime = current_data.get("runtime_ms", "unknown")
        summary += f"\nBaseline Runtime: {runtime} ms\n"
        summary += "Expected Healthy Range: ±10%\n"
        
        # Check for anomalies (heuristic for the summary string)
        anomalies = []
        for table, metrics in current_data["tables"].items():
            # 1. NULLs
            if metrics.get("null_count", 0) > 0:
                anomalies.append(f"NULLs detected in {table}")
            
            # 2. Skew (Absolute & Differential)
            row_count = metrics.get("row_count", 0)
            card = metrics.get("cust_id_cardinality")
            if card:
                # Absolute rule: If extreme
                if row_count > 1000 and card < (row_count / 50): # 2% rule
                    anomalies.append(f"Severe Data Skew detected in {table} (Unique IDs < 2% of rows)")
                
                # Differential rule: If dropped from baseline
                if baseline_ref and "tables" in baseline_ref and table in baseline_ref["tables"]:
                    base_card = baseline_ref["tables"][table].get("cust_id_cardinality")
                    if base_card and base_card > 0:
                        card_drop = (base_card - card) / base_card
                        if card_drop > 0.02: # 2% drop is a red flag
                            anomalies.append(f"Cardinality Drop detected in {table}: {card_drop*100:.1f}% drop from baseline unique count")
            
            # 3. Row count deviations (Duplicates/Skew)
            if baseline_ref and "tables" in baseline_ref and table in baseline_ref["tables"]:
                base_rows = baseline_ref["tables"][table].get("row_count", 0)
                if base_rows > 0:
                    diff = row_count - base_rows
                    change_pct = abs(diff) / base_rows
                    
                    if change_pct > 0.05:
                        # If we are INCREASING rows, it's always an anomaly (unintended growth)
                        # If we are DECREASING rows, it's an anomaly ONLY IF we didn't intend to filter
                        is_problem = True
                        if diff < 0 and intentional_filtering:
                            is_problem = False
                        
                        if is_problem:
                            anomalies.append(f"Unexpected Row Count Change in {table}: {change_pct*100:.1f}% deviation from baseline")

        if anomalies:
            summary += "\nWARNING: Anomalies detected:\n" + "\n".join([f"- {a}" for a in anomalies])
        else:
            summary += "\nNo anomalies detected."
        
        return summary
