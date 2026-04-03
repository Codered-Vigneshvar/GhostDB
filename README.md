# GhostQuery

*A Meta OpenEnv 2026 RL Benchmark*

GhostQuery is a FinOps-focused RL environment designed to benchmark agents against highly inefficient SQL queries. Its goal is to train agents to refactor 'Unoptimized' SQL (Full Table Scans, Cartesian Joins) into 'Optimized' SQL (Predicate Pushdown, Column Pruning) using DuckDB as a high-speed simulation engine. 

Success is measured by the Latency Reduction percentage (`Reward`), but only validated if the resulting dataset maintains **100% bit-fidelity** with the baseline.

## Architecture

- **`models.py`**: Defines strict typed Pydantic structures for `SQLAction`, `SQLObservation` and `SQLState`. 
- **`server/sql_env.py`**: Implementation of `openenv.core.env_server.Environment`.
  - `reset()` populates memory with realistic chaotic data ("Sales").
  - `step(action)` executes agent actions, compares `EXPLAIN ANALYZE` efficiencies, calculates metrics, and enforces bit-fidelity.
- **`grader.py`**: Validates agent outcomes by sorting and hashing stringified `pandas.DataFrame` equivalents using SHA-256. 
- **`baseline.py`**: Contains a zero-shot execution pattern mimicking an AI agent.

## Metrics
- Reward function computes relative efficiency strictly against baseline time.
- `$R = \frac{T_{baseline} - T_{optimized}}{T_{baseline}}$`
- Observations feature exact execution plans (`query_plan_json`) empowering LLM and algorithmic reasoning heuristics.

## Execution

```bash
# Validate local openenv structure
openenv validate

# Run baseline demonstration locally
python baseline.py

# Docker Environment Setup
docker build -t ghostquery .
docker run -p 8000:8000 ghostquery
```
