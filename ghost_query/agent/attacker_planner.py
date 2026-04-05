import json
from typing import Dict, Any, List
from ghost_query.agent.llm_client import LLMClient

class AttackerPlanner:
    def __init__(self):
        self.llm = LLMClient()
        self.allowed_attacks = [
            "duplicate_injection",
            "null_injection",
            "timestamp_shift",
            "join_explosion",
            "skewed_data"
        ]

    def plan_attack(self, project_summary: str) -> Dict[str, Any]:
        """
        Calls LLM to select an attack based on the project summary.
        Returns a validated JSON dictionary.
        """
        prompt = f"""You are an AI system simulating realistic production data issues.

Given the project summary, select ONE realistic attack.

Allowed attacks:
- duplicate_injection
- null_injection
- timestamp_shift
- join_explosion
- skewed_data

Project Summary:
{project_summary}

Return STRICT JSON only:
{{
  "attack_type": "...",
  "target_table": "...",
  "severity": "low|medium|high",
  "reason": "...",
  "expected_impact": "..."
}}
"""
        try:
            response_text = self.llm.generate(prompt)
            # Basic JSON extraction in case of markdown wrapping
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(response_text)
            
            # Validation & Fallback
            if plan.get("attack_type") not in self.allowed_attacks:
                print(f"[PLANNER] Invalid attack type '{plan.get('attack_type')}'. Falling back.")
                return self._get_fallback_plan("Invalid attack type")
                
            return plan
            
        except Exception as e:
            print(f"[PLANNER] Error during planning: {e}. Falling back.")
            return self._get_fallback_plan(str(e))

    def _get_fallback_plan(self, error_msg: str) -> Dict[str, Any]:
        return {
            "attack_type": "null_injection",
            "target_table": "sales",
            "severity": "low",
            "reason": f"Fallback due to planner error: {error_msg}",
            "expected_impact": "Minor data quality issue in sales table."
        }
