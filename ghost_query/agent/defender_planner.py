import json
import re
from typing import Dict, Any, Optional
from ghost_query.agent.llm_client import LLMClient

class DefenderPlanner:
    def __init__(self):
        self.llm = LLMClient()

    def decide_edit(self, context: str) -> Dict[str, Any]:
        """
        Calls LLM to generate a full file replacement fix.
        Returns a validated JSON dictionary.
        """
        system_prompt = """You are an expert data engineer fixing a broken data pipeline.

You are given:
- baseline state (correct system)
- current state after attack
- error logs (if any)
- performance metrics
- previous fix attempts (if any)

Your task:
- FIX the issue by modifying the necessary file in the 'workspace/' directory.

Return STRICT JSON only:
{
  "action": "edit_file",
  "file": "relative_path_in_workspace (e.g., workspace/data/sales.parquet or workspace/dbt_project/models/schema.yml)",
  "new_code": "FULL updated file content",
  "reason": "why this fix works"
}

Rules:
- Only modify necessary files in 'workspace/'.
- Use PLAIN SQL for any .sql files. NEVER use Jinja `{{ }}` or dbt macros.
- MANDATORY: If 'WARNING: Anomalies detected' shows Row Count Change or Data Skew, you MUST perform a DATA-LEVEL repair (UPDATE or CREATE OR REPLACE).
- DO NOT just edit schema.yml if data is corrupt. Editing schema.yml DOES NOT fix skew or duplicates.
- If fixing data skew, identify the outlier ID and redistribute or filter it using a valid SQL pattern.
- If fixing data skew in 'sales.cust_id', use columns: (sale_id, cust_id, amount, sale_time_str).
- Example Fix for Skew: `UPDATE sales SET cust_id = (sale_id % 500000) WHERE cust_id > 900000;`
- Example Fix for Duplicates: `CREATE OR REPLACE TABLE market_trends AS SELECT DISTINCT * FROM market_trends;`
- If previous fixes failed, choose a DIFFERENT approach.
- Do NOT repeat the same fix. Keep code minimal and clean.
"""
        try:
            response_text = self.llm.generate(f"{system_prompt}\n\nContext:\n{context}")
            
            # Clean up potential markdown blocks
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
            
            # Extract JSON 
            start_idx = cleaned_text.find('{')
            end_idx = cleaned_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_part = cleaned_text[start_idx:end_idx+1]
                
                # SPECIAL SANITIZATION:
                # LLMs often put literal newlines inside JSON strings. 
                # We try to escape them or use strict=False
                try:
                    plan = json.loads(json_part, strict=False)
                except json.JSONDecodeError:
                    # Fallback: very aggressive cleaning
                    # Replace literal newlines in what looks like the new_code block
                    # This is risky but helps with common LLM failure modes
                    print(f"[PLANNER] Aggressive cleaning triggered for: {json_part[:100]}...")
                    # We'll try to escape the contents of the last block if it was unclosed
                    plan = json.loads(json_part.replace('\n', '\\n'), strict=False)
            else:
                plan = json.loads(cleaned_text, strict=False)
                
            # Basic Safety Check
            target_file = plan.get("file", "")
            if not target_file.startswith("workspace/"):
                return self._get_fallback_error(f"Invalid target path: {target_file}. Only 'workspace/' is allowed.")
                
            return plan
            
        except Exception as e:
            return self._get_fallback_error(str(e))

    def _get_fallback_error(self, error_msg: str) -> Dict[str, Any]:
        return {
            "action": "error",
            "reason": f"Planner failed: {error_msg}",
            "file": None,
            "new_code": None
        }
