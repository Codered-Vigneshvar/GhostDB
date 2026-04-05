import os
from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.defender_agent import DefenderAgent
from ghost_query.agent.evaluator_agent import EvaluatorAgent

def test_full_game_loop():
    print("--- 1. Resetting Environment ---")
    rm = ResetManager()
    rm.reset_workspace(seed=42)
    
    engine = DBEngine()
    
    print("\n--- 2. Sabotaging DB (Attacker) ---")
    attacker = AttackerAgent(engine)
    # Generates a duplicate_injection or timestamp_shift natively
    attack_res = attacker.generate_attack(seed=42)
    round_id = attack_res["round_id"]
    
    print("\n--- 3. Autonomous Healing (Defender) ---")
    defender = DefenderAgent(engine)
    defense_res = defender.run_defense(round_id=round_id)
    
    print("\n--- 4. Pure Deterministic Grading (Evaluator) ---")
    evaluator = EvaluatorAgent(engine)
    score_res = evaluator.evaluate(round_id)
    
    print(f"\n✅ ROUND {round_id} ENDED WITH FINAL SCORE: {score_res['final_score']}")
    print(f"Match status: {score_res['status']}")
    
    assert score_res["final_score"] > 0.8, "The Defender should have scored near aggressively perfect cleanly!"
    engine.close()

if __name__ == "__main__":
    test_full_game_loop()
