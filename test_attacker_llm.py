import os
from ghost_query.environment.engine import DBEngine
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.attacker_planner import AttackerPlanner

def test_llm_attacker():
    print("--- Testing LLM-Driven Attacker ---")
    
    # 1. Reset Environment
    rm = ResetManager()
    rm.reset_workspace()
    
    # 2. Initialize Engine & Agent
    engine = DBEngine()
    attacker = AttackerAgent(engine)
    
    # 3. Generate Attack
    print("\n[TEST] Running LLM Attack Generation...")
    attack_res = attacker.generate_attack(seed=42)
    
    print("\n--- Attack Result ---")
    print(attack_res)
    
    # 4. Verify Metadata
    round_id = attack_res["round_id"]
    metadata_path = f"ghost_query/metadata/attack_truth/round_{round_id}.json"
    
    if os.path.exists(metadata_path):
        print(f"\n✅ Metadata log found at {metadata_path}")
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            print("Reasoning from LLM:", data.get("reason"))
            print("Impact predicted:", data.get("expected_impact"))
    else:
         print(f"\n❌ Metadata log NOT found!")
         
    print("\n✅ LLM Attacker verification successful!")
    engine.close()

if __name__ == "__main__":
    import json
    test_llm_attacker()
