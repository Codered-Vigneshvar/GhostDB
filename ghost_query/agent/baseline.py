from ghost_query.environment.sql_env import SQLEnv
from ghost_query.models import SQLAction

def main():
    print("Initializing GhostQuery Zero-Shot Evaluation (Modular Structure)...")
    env = SQLEnv()
    
    obs, state, info = env.reset()
    
    print("\n[SCENE]: Database initialized with 100k messy rows via DBEngine.")
    print(f"Baseline Latency: {obs.latency_ms:.2f} ms")
    
    optimized_query = """
        SELECT 
            s1.region_id, 
            COUNT(DISTINCT s1.transaction_id) as total_txns, 
            SUM(s1.amount) as total_sales
        FROM Sales s1
        INNER JOIN Sales s2 ON s1.status = s2.status
        WHERE s1.status ILIKE '%completed%'
        GROUP BY s1.region_id
    """
    print(f"Executing Optimized Query:\n{optimized_query}")
    
    action = SQLAction(sql_query=optimized_query)
    next_obs, reward, terminated, truncated, info = env.step(action)
    
    print("\n--- RESULTS ---")
    print(f"New Latency: {next_obs.latency_ms:.2f} ms")
    
    if 'error' in info:
        print(f"Penalty Applied: {reward} ({info.get('error')}: {info.get('reason')})")
    else:
        print(f"Reward: {reward:.4f} ({info.get('status')}: {info.get('reason')})")

if __name__ == "__main__":
    main()
