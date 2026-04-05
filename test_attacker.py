import os
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent

def test_attacker():
    print("--- 1. Resetting Workspace ---")
    resetter = ResetManager()
    resetter.reset_workspace(seed=999)
    
    print("\n--- 2. Initializing DB Engine ---")
    engine = DBEngine()
    
    print("\n--- 3. Running AttackerAgent ---")
    attacker = AttackerAgent(engine)
    
    # Run the attack
    result = attacker.generate_attack(seed=12)
    print(f"\nAttack Result: {result}")
    
    engine.close()

if __name__ == "__main__":
    test_attacker()
