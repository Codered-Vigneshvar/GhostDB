# GHOSTQUERY: Meta OpenEnv 2026 Master Constitution
# Purpose: Pass the Round 1 Programmatic & LLM Evaluation

## 1. CORE API & REWARD LOOP (NON-NEGOTIABLE)
- Inherit from `openenv.core.env_server.Environment`.
- **reset() -> Observation**: Must initialize the DuckDB sandbox and return the first state.
- **step(action: Action) -> StepResult**:
    - MUST return: `(observation: Observation, reward: float, done: bool, info: dict)`.
    - **Reward Formula**: Use `(Baseline_Time - New_Time) / Baseline_Time`.
    - **Penalties**: -1.0 for Syntax Errors or Result Mismatches.
- **state() -> State**: Must return the full hidden metadata for the automated grader.

## 2. PROJECT ARCHITECTURE & FILES
- **openenv.yaml**: Must include `entry_point`, `version`, and `tags: ["sql-optimization", "finops"]`.
- **models.py**: Use strictly typed Pydantic models for ALL Actions/Observations.
- **server/app.py**: Use `openenv.core.env_server.create_fastapi_app` for the server.
- **pyproject.toml**: Include all dependencies (duckdb, openenv-core, pydantic).

## 3. DOCKER & PORTABILITY
- **Base Image**: `python:3.11-slim`.
- **Port**: Must listen on port `8000`.
- **Self-Contained**: Include all dummy CSV/Parquet data inside the Docker image. No external API keys.

## 4. HUGGING FACE SUBMISSION (ROUND 1)
- The final environment must be pushed using the CLI: `openenv push`.
- The repository must include a `README.md` that serves as a "Research Spec" for LLM Scoring.
- Evaluation includes:
    1. **Programmatic Check**: Does the Docker run and the API work?
    2. **LLM Scoring**: Is the reasoning feedback in the Observation high-quality?

## 5. VALIDATION GUARDRAIL
- Always run `openenv validate .` before asking for a code review.