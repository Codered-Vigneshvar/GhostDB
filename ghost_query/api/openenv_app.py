import os
import uuid
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ghost_query.environment.reset_manager import ResetManager
from ghost_query.environment.engine import DBEngine
from ghost_query.agent.attacker_agent import AttackerAgent
from ghost_query.agent.defender_agent import DefenderAgent
from ghost_query.agent.evaluator_agent import EvaluatorAgent
from ghost_query.environment.baseline_runner import BaselineRunner
import json

app = FastAPI(title="GhostQuery OpenEnv Arena")

# Global State / Singletons
engine = DBEngine()
reset_manager = ResetManager()
attacker = AttackerAgent(engine)
defender = DefenderAgent(engine)
evaluator = EvaluatorAgent(engine)
baseline_runner = BaselineRunner(engine)

session_state = {
    "round_id": None,
    "status": "idle",
    "result": None,
    "seed": None
}

class ResetRequest(BaseModel):
    seed: Optional[int] = 42

class StepRequest(BaseModel):
    pass

@app.post("/reset")
async def reset(req: ResetRequest):
    """
    Cleans the workspace and prepares for a new round.
    """
    try:
        seed = req.seed
        reset_res = reset_manager.reset_workspace(seed=seed)
        
        # New Round ID
        round_id = uuid.uuid4().hex[:8]
        
        session_state["round_id"] = round_id
        session_state["status"] = "idle"
        session_state["result"] = None
        session_state["seed"] = seed
        
        # CAPTURE HEALTHY BASELINE
        print(f"[BASELINE] Capturing initial healthy metrics...")
        healthy_metrics = baseline_runner.run_baseline()
        with open("ghost_query/metadata/baseline_metrics.json", "w") as f:
            json.dump(healthy_metrics, f)
        
        print(f"[START] round_id={round_id}")
        
        return {
            "round_id": round_id,
            "status": "idle"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step")
async def step():
    """
    Executes the full simulation: Attack -> Defend -> Evaluate.
    """
    if not session_state["round_id"]:
        raise HTTPException(status_code=400, detail="No active session. Call /reset first.")
    
    if session_state["status"] == "done":
         raise HTTPException(status_code=400, detail="Round already completed. Call /reset for a new round.")

    round_id = session_state["round_id"]
    seed = session_state["seed"]
    
    try:
        # 1. Attack
        print(f"[STEP] action=attack")
        attacker.generate_attack(seed=seed, round_id=round_id)
        
        # 2. Defend
        print(f"[STEP] action=defense")
        defense_res = defender.run_defense(round_id=round_id)
        
        # 3. Evaluate
        print(f"[STEP] action=evaluation")
        eval_res = evaluator.evaluate(round_id=round_id)
        
        session_state["status"] = "done"
        session_state["result"] = eval_res
        
        print(f"[END] score={eval_res.get('final_score')}")
        
        return {
            "round_id": round_id,
            "status": "done",
            "result": eval_res
        }
    except Exception as e:
        session_state["status"] = "failed"
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state")
async def state():
    """
    Returns the current benchmark state.
    """
    return session_state

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
