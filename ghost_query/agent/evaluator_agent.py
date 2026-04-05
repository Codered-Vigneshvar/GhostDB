import os
import json
from typing import Dict, Any

class EvaluatorAgent:
    def __init__(self, engine):
        self.engine = engine
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.metadata_dir = os.path.join(os.path.dirname(current_dir), "metadata")
        self.reports_dir = os.path.join(os.path.dirname(current_dir), "reports")
        
        # Paths
        self.truth_dir = os.path.join(self.metadata_dir, "attack_truth")
        self.defender_logs_dir = os.path.join(self.metadata_dir, "round_logs")
        self.scorecards_dir = os.path.join(self.metadata_dir, "scorecards")
        self.match_results_dir = os.path.join(self.reports_dir, "match_results")
        
        os.makedirs(self.scorecards_dir, exist_ok=True)
        os.makedirs(self.match_results_dir, exist_ok=True)

    def evaluate(self, round_id: str) -> Dict[str, Any]:
        print(f"\n[EVAL] Round {round_id}")
        
        try:
            truth = self._load_attack_truth(round_id)
            report = self._load_defender_report(round_id)
        except Exception as e:
            print(f"[EVAL] Error loading data: {e}")
            raise e
            
        metrics = self._compute_metrics(truth, report)
        final_score = self._compute_score(metrics)
        
        status = "resolved" if final_score > 0.3 else "failed"
        
        print(f"[EVAL] Score: {final_score:.2f}")
        print(f"[EVAL] Status: {status}")
        
        result = {
            "round_id": round_id,
            "attack_type": truth.get("attack_type", "unknown"),
            "detected": metrics["detection"],
            "fixed": metrics["fix"],
            "efficiency_score": metrics["efficiency"],
            "final_score": final_score,
            "status": status
        }
        
        # Save JSON scorecard
        scorecard_path = os.path.join(self.scorecards_dir, f"round_{round_id}.json")
        with open(scorecard_path, "w") as f:
            json.dump(result, f, indent=4)
            
        # Save Markdown Report
        self._generate_match_report(result)
        
        return result

    def _load_attack_truth(self, round_id: str) -> Dict[str, Any]:
        path = os.path.join(self.truth_dir, f"round_{round_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing attack truth for round {round_id}")
        with open(path, "r") as f:
            return json.load(f)

    def _load_defender_report(self, round_id: str) -> Dict[str, Any]:
        path = os.path.join(self.defender_logs_dir, f"round_{round_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing defender structured logs for round {round_id}")
        with open(path, "r") as f:
            return json.load(f)

    def _compute_metrics(self, truth: Dict[str, Any], report: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Detection: Did the defender identify the correct table and issue?
        attack_type = truth.get("attack_type", "")
        target_table = truth.get("target_table", "")
        
        detected = False
        history = report.get("history", [])
        for attempt in history:
            reason = attempt.get("reason", "").lower()
            # If the reason mentions the table and the attack type (or synonym)
            if target_table.lower() in reason and (attack_type.lower() in reason or "fix" in reason):
                detected = True
                break

        # 2. Fix constraint verification (Database state)
        fixed_correctly = False
        try:
            # Check NULLs
            null_count = self.engine.execute("SELECT COUNT(*) FROM sales WHERE amount IS NULL").fetchone()[0]
            
            # Check Duplicates
            dupe_count = self.engine.execute("SELECT COUNT(*) FROM (SELECT segment, trend_index, detail_padding FROM market_trends GROUP BY segment, trend_index, detail_padding HAVING COUNT(*) > 1)").fetchone()[0]
            
            # Check Timestamp Shift
            max_date = self.engine.execute("SELECT MAX(CAST(sale_time_str AS TIMESTAMP)) FROM sales").fetchone()[0]
            date_ok = str(max_date) <= "2026-04-01 23:59:59" if max_date else True

            # Check Skew (e.g., in sales.cust_id)
            skew_count = 0
            if attack_type == "skewed_data":
                # Lowered threshold to 50k to catch subtle mutations
                skew_query = "SELECT COUNT(*) FROM (SELECT cust_id FROM sales GROUP BY cust_id HAVING COUNT(*) > 50000)"
                skew_count = self.engine.execute(skew_query).fetchone()[0]

            fixed_correctly = (null_count == 0) and (dupe_count == 0) and date_ok and (skew_count == 0)
        except Exception:
            fixed_correctly = False

        # 3. Efficiency (Max 0.2)
        # Fewer attempts -> higher score
        attempts = len(history)
        if attempts == 0:
            eff_score = 0.0
        else:
            eff_score = round(max(0.05, 0.2 / attempts), 2)
            
        # 4. Consistency
        consistency = detected and fixed_correctly
        
        return {
            "detection": detected,
            "fix": fixed_correctly,
            "efficiency": eff_score if fixed_correctly else 0.0,
            "consistency": consistency
        }

    def _compute_score(self, metrics: Dict[str, Any]) -> float:
        score = 0.0
        if metrics["detection"]:
            score += 0.2
        if metrics["fix"]:
            score += 0.5
        score += metrics["efficiency"]
        if metrics["consistency"]:
            score += 0.1
            
        return round(score, 2)

    def _generate_match_report(self, result: Dict[str, Any]):
        md_content = f"""# Match Result

## Round Summary
**Round ID:** {result['round_id']}
**Attack Type Enacted:** {result['attack_type']}
**Defender Detected Root Cause:** {result['detected']}
**DB Physically Healed:** {result['fixed']}

## Score Breakdown
- **Detection (Max 0.2):** {0.2 if result['detected'] else 0.0}
- **Fix Constraints (Max 0.5):** {0.5 if result['fixed'] else 0.0}
- **Efficiency (Max 0.2):** {result['efficiency_score']}
- **Consistency (Max 0.1):** {0.1 if (result['fixed'] and result['detected']) else 0.0}

**Final Mathematical Score:** {result['final_score']}

## Verdict
> **{result['status'].upper()}**
"""
        filepath = os.path.join(self.match_results_dir, f"round_{result['round_id']}.md")
        with open(filepath, "w") as f:
            f.write(md_content)
