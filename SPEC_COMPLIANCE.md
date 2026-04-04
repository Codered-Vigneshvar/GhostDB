# GHOSTQUERY: 2026 Hackathon Spec Compliance
# Purpose: Ensure 100% pass rate for Meta/HuggingFace Programmatic Evaluation

## 1. RUNTIME & LIBRARIES
- **Python Version:** MUST use `python:3.11-slim` as the base image for the Dockerfile.
- **Core Library:** `openenv-core` is the mandatory interface. Use `pip install openenv-core` in requirements.
- **Server:** MUST use **FastAPI** with `uvicorn` to serve the environment inside the container.
- **Database:** Use `duckdb` (v1.2+ for 2026 performance features) for the optimization sandbox.

## 2. GYMNASIUM-STYLE API CONTRACT
Every environment MUST implement the following specific signatures:
- `reset(seed: Optional[int] = None, options: Optional[dict] = None) -> (Observation, info: dict)`
- `step(action: Action) -> (Observation, reward: float, terminated: bool, truncated: bool, info: dict)`
  - *Note:* In 2026, OpenEnv uses the **Terminated/Truncated** dual-flag system like Gymnasium 1.0+.
- `state() -> State`: Returns the ground truth metadata for the grader.

## 3. NETWORKING & PORTS
- **Default Port:** The FastAPI server MUST listen on **Port 8000**.
- **Endpoint:** The environment must expose the `/step`, `/reset`, and `/state` endpoints via the `openenv.core.env_server.create_fastapi_app` helper.

## 4. HUGGING FACE HUB STANDARDS
- **Metadata:** `openenv.yaml` MUST define the `task_type` as `data_engineering` and include the `evaluation_metric` key set to `latency_reduction_percent`.
- **README:** Must follow the "Research Spec" format: Abstract -> Environment State Space -> Action Space -> Reward Logic -> Baseline Results.

## 5. REPRODUCIBILITY (THE "SCIENTIST" RULE)
- **Zero-External Calls:** The environment MUST NOT require an internet connection or external API keys (like OpenAI/Anthropic) to run. All AI logic for the environment (like graders) must be local or mockable.
- **Static Assets:** All DuckDB files or Parquet datasets must be copied into the Docker image during the `build` phase, not downloaded at runtime.