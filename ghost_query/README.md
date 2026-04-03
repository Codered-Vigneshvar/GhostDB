# GhostQuery: THE VISION (Research Abstract)

GhostQuery is a Meta OpenEnv 2026 RL Benchmark for SQL Optimization. It trains agents to refactor 'Unoptimized' SQL (Full Table Scans, Cartesian Joins) into 'Optimized' SQL (Predicate Pushdown, Column Pruning) using DuckDB as a high-speed simulation engine.

## PROJECT STARTER STRUCTURE

- **`ghost_query/environment/`**: THE WORLD (Teammate's Focus)
  - `sql_env.py`: Core Logic: Inherits from `openenv.Environment`.
  - `grader.py`: The Referee: Hashing and Data Integrity.
  - `engine.py`: DuckDB session & Parquet loading.
- **`ghost_query/agent/`**: THE BRAIN (Your Focus)
  - `baseline.py`: The RL Loop: Talks to the FastAPI server.
  - `researcher.py`: LLM Logic: How the agent "thinks".
  - `prompts.py`: System instructions for SQL optimization.
- **`ghost_query/data/`**: THE MATTER (Static Assets)
  - `sales_data.parquet`: 1M rows of unoptimized data.
  - `customers.parquet`: Dimension tables.
- **`ghost_query/tasks/`**: THE QUESTS (Challenge Files)
  - `task_1_joins.sql`: Specific SQL "traps" for the agent.
  - `task_2_ctes.sql`.
- **`ghost_query/models.py`**: THE CONTRACT (Shared Schemas).
- **`ghost_query/app.py`**: THE GATEWAY (FastAPI Server Entry).
- **`ghost_query/Dockerfile`**: THE CONTAINER (The "Glass Box").
- **`ghost_query/pyproject.toml`**: THE MANIFEST (Dependencies).

## EXECUTION

Run the zero-shot baseline loop:
```bash
python3 -m ghost_query.agent.baseline
```

Deploy the FastAPI Gateway:
```bash
uvicorn ghost_query.app:app --host 0.0.0.0 --port 8000
```
