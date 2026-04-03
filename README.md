# GhostQuery

*A Meta OpenEnv 2026 RL Benchmark for SQL Optimization*

GhostQuery is a modular RL environment designed to train agents in sophisticated SQL refactoring. It uses DuckDB for high-speed simulation and enforces 100% bit-fidelity via SHA-256 result set hashing.

## Project Structure

```text
ghost_query/
├── environment/           # THE WORLD (Environment Logic)
│   ├── sql_env.py        # Core Logic: RL execution and Reward calculation
│   ├── grader.py         # The Referee: Bit-fidelity validation
│   └── engine.py         # DuckDB session & Data management
│
├── agent/                 # THE BRAIN (Agent Intelligence)
│   ├── baseline.py       # The RL Loop: Entrypoint for local evaluation
│   ├── researcher.py     # LLM Logic: SQL reasoning heuristics
│   └── prompts.py        # System instructions and few-shots
│
├── data/                  # THE MATTER (Static Assets)
│   ├── sales_data.parquet # Evaluation datasets
│   └── customers.parquet  
│
├── tasks/                 # THE QUESTS (Challenge Files)
│   ├── task_1_joins.sql  # Specific SQL optimization scenarios
│   └── task_2_ctes.sql
│
├── models.py              # THE CONTRACT (Strict Typed Schemas)
└── app.py                 # THE GATEWAY (FastAPI Server Entrypoint)
```

## Getting Started

### Local Evaluation
Run the zero-shot baseline loop to verify the environment:
```bash
python -m ghost_query.agent.baseline
```

### Server Deployment
Launch the environment as a FastAPI microservice:
```bash
uvicorn ghost_query.app:app --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t ghost_query .
docker run -p 8000:8000 ghost_query
```
