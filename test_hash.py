import sys
import os
sys.path.append(os.getcwd())
from ghost_query.environment.sql_env import SQLEnv
from ghost_query.models import SQLAction

env = SQLEnv()
env.reset()

with open('ghost_query/tasks/slow_query_1.sql', 'r') as f:
    env.baseline_query = f.read()
env.current_task_name = 'slow_query_1.sql'

obs, latency = env._execute_query(env.baseline_query)
env.baseline_latency_ms = latency

with open('ghost_query/agent/AgentCode/slow_query_1.gn', 'r') as f:
    opt_sql = f.read()

action = SQLAction(sql_query=opt_sql)
next_obs, reward, terminated, truncated, info = env.step(action)

from ghost_query.environment.grader import verify_integrity

print(f"Is valid via env: {next_obs.is_valid}")

df_orig = env.baseline_df
df_opt = env.engine.execute(opt_sql).df()
print(f"Lengths: Orig={len(df_orig)}, Opt={len(df_opt)}")

if len(df_orig) == len(df_opt):
    for col in df_orig.columns:
        if not df_orig[col].equals(df_opt[col]):
            print(f"Mismatch in column: {col}")
            print(f"Orig: {df_orig[col].head(3).tolist()}")
            print(f"Opt: {df_opt[col].head(3).tolist()}")
            break
