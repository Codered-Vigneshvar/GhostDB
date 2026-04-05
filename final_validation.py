from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.defender_agent import DefenderAgent
from ghost_query.agent.evaluator_agent import EvaluatorAgent

def validate():
    # Initialize shared engine for state consistency
    engine = DBEngine()
    
    rm = ResetManager()
    rm.reset_workspace(seed=42)

    attacker = AttackerAgent(engine)
    attack = attacker.generate_attack(seed=42)

    defender = DefenderAgent(engine)
    defender.run_defense(round_id=attack["round_id"])

    evaluator = EvaluatorAgent(engine)
    result = evaluator.evaluate(round_id=attack["round_id"])

    print("\n--- FINAL RESULT ---")
    print(result)
    engine.close()

if __name__ == "__main__":
    validate()
