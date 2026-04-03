# Building with GhostQuery: A Step-by-Step Guide

This document clearly outlines how to use the provided GhostQuery starter code.

## 1. THE WORLD: DB Simulation (`ghost_query/environment/`)
- **`engine.py`**: Manages the DuckDB physics. Expand this to load the 1M row `sales_data.parquet` and `customers.parquet` from **THE MATTER** (`ghost_query/data/`).
- **`sql_env.py`**: Defies the state of the world. Update `reset()` to initialize specific **QUESTS** from `ghost_query/tasks/`.
- **`grader.py`**: Ensures the bit-fidelity "Referee" logic is sound by hashing result sets.

## 2. THE BRAIN: Agent Integration (`ghost_query/agent/`)
- **`baseline.py`**: The RL Loop. This is where your agent interacts with **THE GATEWAY**.
- **`researcher.py` & `prompts.py`**: This is where you implement the "Thinking" logic. Use the `query_plan_json` from the `SQLObservation` to reason about optimizations.

## 3. THE CONTRACT: API Schemas (`ghost_query/models.py`)
Ensure your agent emits `SQLAction` and parses `SQLObservation` as defined in the contract.

---

### Deployment: THE CONTAINER (`ghost_query/Dockerfile`)
The environment is containerized as a FastAPI server. Build and run to start the simulation node.
```bash
docker build -t ghost_query .
docker run -p 8000:8000 ghost_query
```
