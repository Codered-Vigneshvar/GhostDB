import os
import glob
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.defender_agent import DefenderAgent

def test_defense():
    print("--- 1. Workspace Reset ---")
    rm = ResetManager()
    rm.reset_workspace()
    
    engine = DBEngine()
    
    print("\n--- 2. Attacking the DB ---")
    attacker = AttackerAgent(engine)
    # Using seed 901 as a random test seed to trigger some attack
    attack_res = attacker.generate_attack(seed=901)
    
    print("\n--- 3. Engaging DefenderAgent ---")
    defender = DefenderAgent(engine)
    defense_res = defender.run_defense()
    
    print("\n--- 4. Evaluating Outcome ---")
    print(f"Attack injected: {attack_res['attack_type']}")
    print(f"Defender localized: {defense_res['root_cause']}")
    assert defense_res["validation"]["fixed"] == True, "Defender failed to clean up the attack!"
    
    print("\n--- 5. Checking Reports ---")
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ghost_query", "reports", "incident_reports")
    reports = glob.glob(os.path.join(reports_dir, "*.md"))
    print(f"Found auto-generated Incident Reports: {reports}")
    assert len(reports) > 0, "No markdown report was generated!"
    
    print("\n✅ Defender Validation successful!")
    engine.close()

if __name__ == "__main__":
    test_defense()
