from ghost_query.environment.sql_env import SQLEnv
from ghost_query.models import SQLAction
import os

def main():
    print("Initializing GhostQuery Zero-Shot Agent (Strict Protocol Compliance)...")
    env = SQLEnv()
    
    obs, state, info = env.reset()
    task_name = info.get("task", "unknown")
    
    print(f"\n[SCENE]: Database and Parquets dynamically loaded.")
    print(f"Current Task: {task_name}")
    print(f"Baseline Latency: {obs.baseline_latency:.2f} ms")
    
    # Send the baseline back as the action to test the pipeline (zero-shot dummy agent)
    # In full release, this goes to Gemini (researcher.py).
    optimized_query = obs.original_sql
    
    print(f"Simulating Agent LLM Reasoning... (Dummy Pass-through)")
    
    action = SQLAction(sql_query=optimized_query)
    next_obs, reward, terminated, truncated, info = env.step(action)
    
    print("\n--- RESULTS ---")
    print(f"New Latency: {next_obs.latency_ms:.2f} ms")
    print(f"Reward: {reward:.4f} ({info.get('status', info.get('error'))}: {info.get('reason')})")

    # Generate the SUMMARY.md Artifact
    summary_content = f"""# Agent Task Summary: {task_name}
    
## Metrics
| Metric | Original | Optimized | Improvement |
|---|---|---|---|
| Latency | {obs.baseline_latency:.2f} ms | {next_obs.latency_ms:.2f} ms | {reward * 100:.2f}% |

## Agent Reasoning
*Since this is the baseline dummy agent, I returned the original query without modifications to ensure the pipeline and integrity checking hash perfectly aligns.*

## Query Plans
### Original Plan
```json
{obs.query_plan_json}
```

### Optimized Plan
```json
{next_obs.query_plan_json}
```
"""
    with open("SUMMARY.md", "w") as f:
        f.write(summary_content)
    print("\n✅ Artifact generated: SUMMARY.md")

if __name__ == "__main__":
    main()
