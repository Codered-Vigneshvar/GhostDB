import json
from typing import Dict, Any, List

class DefenderContext:
    def __init__(self, baseline_summary: str):
        self.baseline_summary = baseline_summary

    def build_context(self, current_metrics: Dict[str, Any], attempt_history: List[Dict[str, Any]], error_logs: List[str]) -> str:
        """
        Constructs a unified prompt string for the LLM.
        """
        history_str = ""
        if attempt_history:
            history_str = "\n--- Attempt History ---\n"
            for i, attempt in enumerate(attempt_history):
                history_str += f"Attempt {i+1}:\n"
                history_str += f"- File modified: {attempt.get('file')}\n"
                history_str += f"- Reason: {attempt.get('reason')}\n"
                if attempt.get('error'):
                    history_str += f"- Error encountered: {attempt.get('error')}\n"
                else:
                    history_str += f"- Status: Success (but validation failed or metrics still off)\n"

        errors_str = ""
        if error_logs:
            errors_str = "\n--- Recent System Errors ---\n" + "\n".join(error_logs[-3:])

        context = f"""[BASELINE SYSTEM STATE]
{self.baseline_summary}

[CURRENT SYSTEM STATE (DEGRADED)]
Row Counts: {current_metrics.get('tables', 'Unknown')}
Runtime: {current_metrics.get('runtime_ms', 'Unknown')} ms
{errors_str}
{history_str}

[INSTRUCTION]
Analyze the difference between the baseline and current state. 
Identify the most likely entry point for the corruption or performance regression.
Generate a FULL replacement for the necessary file within the 'workspace/' directory.
DO NOT repeat failed fixes from the history.
IF previous fixes failed, try a different approach or target a different file (e.g., if a SQL fix failed, check if a script was modified).
"""
        return context
