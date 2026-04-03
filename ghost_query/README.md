# GhostQuery: THE VISION (Research Abstract)

GhostQuery is a Meta OpenEnv 2026 RL Benchmark for SQL Optimization. It trains agents to refactor 'Unoptimized' SQL (Full Table Scans, Cartesian Joins) into 'Optimized' SQL (Predicate Pushdown, Column Pruning) using DuckDB as a high-speed simulation engine.

## PROJECT STARTER STRUCTURE

```text
ghost_query/
├── environment/           # THE WORLD (Teammate's Focus)
│   ├── __init__.py
│   ├── sql_env.py        # Core Logic: RL execution and Reward calculation
│   ├── grader.py         # The Referee: Bit-fidelity validation
│   └── engine.py         # DuckDB session & Data management
├── agent/                 # THE BRAIN (Your Focus)
│   ├── __init__.py
│   ├── baseline.py       # The RL Loop: Entrypoint for local evaluation
│   ├── researcher.py     # LLM Logic: SQL reasoning heuristics
│   └── prompts.py        # System instructions and few-shots
├── data/                  # THE MATTER (Static Assets)
│   ├── sales_data.parquet # Evaluation datasets
│   └── customers.parquet  
├── tasks/                 # THE QUESTS (Challenge Files)
│   ├── task_1_joins.sql  # Specific SQL optimization scenarios
│   └── task_2_ctes.sql
├── models.py              # THE CONTRACT (Strict Typed Schemas)
├── app.py                 # THE GATEWAY (FastAPI Server Entrypoint)
├── Dockerfile             # THE CONTAINER (The "Glass Box")
├── pyproject.toml         # THE MANIFEST (Dependencies)
└── README.md              # THE VISION (Research Abstract)
```

## EXECUTION

Run the zero-shot baseline loop:
```bash
python3 -m ghost_query.agent.baseline
```

Deploy the FastAPI Gateway:
```bash
uvicorn ghost_query.app:app --host 0.0.0.0 --port 8000
```
