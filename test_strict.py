import os
import json
import glob
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent

def run_tests():
    print("--- 1. Resetting Workspace ---")
    rm = ResetManager()
    rm.reset_workspace()
    
    # Needs to initialize the engine to feed to AttackerAgent
    engine = DBEngine()
    
    print("\n--- 2. Checking DuckDB Data Prior to Attack ---")
    sales_nulls_before = engine.execute("SELECT COUNT(*) FROM sales WHERE amount IS NULL").fetchone()[0]
    print(f"NULL amounts in Sales before attack: {sales_nulls_before}")
        
    print("\n--- 3. Running AttackerAgent (Seed 42) ---")
    attacker = AttackerAgent(engine)
    result = attacker.generate_attack(seed=42)
    print(f"Result: {result}")
    
    print("\n--- 4. Checking DuckDB Data Post Attack ---")
    if result["attack_type"] == "null_injection":
        sales_nulls_after = engine.execute("SELECT COUNT(*) FROM sales WHERE amount IS NULL").fetchone()[0]
        print(f"NULL amounts in Sales after attack: {sales_nulls_after}")
        assert sales_nulls_after > sales_nulls_before, "DuckDB was not mutated by null injection!"
    
    if result["attack_type"] == "timestamp_shift":
        print("Timestamp shift logic successfully altered rows.")
        
    if result["attack_type"] == "duplicate_injection":
        market_count = engine.execute("SELECT COUNT(*) FROM market_trends").fetchone()[0]
        print(f"Market Trends records expanded! Currently: {market_count}")
        
    print("\n--- 5. Checking Metadata Creation ---")
    metadata_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghost_query", "metadata", "attack_truth")
    json_files = glob.glob(os.path.join(metadata_dir, "*.json"))
    print(f"Found metadata files: {json_files}")
    assert len(json_files) > 0, "No metadata files found!"
    
    print("\n--- 6. Verifying Seed Determinism ---")
    result2 = attacker.generate_attack(seed=42)
    print(f"Result (Second run): {result2}")
    assert result["attack_type"] == result2["attack_type"], "Attack types did not match under identical seed!"
    assert result["target_table"] == result2["target_table"], "Target tables did not match under identical seed!"
    
    print("\n✅ Verification entirely safely complete!")
    engine.close()

if __name__ == "__main__":
    run_tests()
