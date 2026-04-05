import os
import json
from ghost_query.environment.engine import DBEngine
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.defender_agent import DefenderAgent

def test_defender_full_edit():
    print("--- Testing Autonomous Full-Edit Defender ---")
    
    # 1. Reset Environment
    rm = ResetManager()
    rm.reset_workspace()
    
    # 2. Initialize Engine
    engine = DBEngine()
    
    # 3. Inject Attack (Randomly picked by LLM)
    print("\n[TEST] Phase 1: Injecting Attack...")
    attacker = AttackerAgent(engine)
    attack_res = attacker.generate_attack(seed=123) # Seed for reproducibility if LLM allows
    round_id = attack_res["round_id"]
    
    # 4. Run Autonomous Defender
    print("\n[TEST] Phase 2: Launching Autonomous AI Engineer (Defender)...")
    defender = DefenderAgent(engine)
    defense_res = defender.run_defense(max_retries=6, round_id=round_id)
    
    print("\n--- Final Results ---")
    print(f"Round ID: {defense_res['round_id']}")
    print(f"Success: {defense_res['success']}")
    print(f"Attempts: {defense_res['attempts']}")
    print(f"Runtime Delta: {defense_res['runtime_before']}ms -> {defense_res['runtime_after']}ms")
    
    # 5. Check Report
    report_path = f"ghost_query/reports/incident_reports/round_{round_id}.md"
    if os.path.exists(report_path):
        print(f"\n✅ Incident Report generated: {report_path}")
    else:
        print(f"\n❌ Incident Report NOT found!")

    # 6. Check Logic
    if defense_res["success"]:
        print("\n✅ Defender successfully reasoning and coding its way to a fix!")
    else:
        print("\n⚠️ Defender failed to resolve within retry limit (check logs for errors).")

    engine.close()

if __name__ == "__main__":
    test_defender_full_edit()
