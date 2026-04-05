# GhostQuery: THE VISION (Research Abstract)

GhostQuery is a Meta OpenEnv 2026 RL Benchmark for SQL Optimization. It trains agents to refactor 'Unoptimized' SQL (Full Table Scans, Cartesian Joins) into 'Optimized' SQL (Predicate Pushdown, Column Pruning) using DuckDB as a high-speed simulation engine.

## MULTI-AGENT ARCHITECTURE

GhostQuery uses an adversarial AI architecture to simulate, test, and optimize SQL:
- **Attacker Agent**: Injects realistic data problems, schema drifts, and noise.
- **Defender Agent**: Monitors the environment, diagnoses regressions, and patches SQL.
- **Evaluator Agent**: Grades the interactions and maintains bit-fidelity validation.

## DIRECTORY STRUCTURE (Baseline vs Workspace)

The system enforces strict state management to prevent corruption:
- `baseline/`: The immutable ground truth. Contains the snapshot of the dbt project and the original `.parquet` data.
- `workspace/`: The volatile arena. Agents interact, mutate, and execute inside this folder. The `ResetManager` populates the workspace from the baseline at the start of each round.

```text
ghost_query/
├── agent/                 # The Agents (Attacker, Defender, Evaluator)
├── environment/           # The System Managers (ResetManager, StateStore, Permissions)
├── baseline/              # Immutable "Ground Truth"
├── workspace/             # Mutable Execution Arena
├── reports/               # Match Results and Incident Reports
├── metadata/              # Round Logs and Attack Proofs
├── schemas/               # Agent Output JSON Schemas
├── models.py              # The Contract (Strict Typed Schemas)
└── data/                  # Generative Scripts
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

## LLM Configuration

GhostQuery seamlessly switches between an autonomous OpenAI-compatible API and a Groq fallback engine for inference depending on environmental states. 

To govern the LLM, declare the following environment variables (such as in an `.env` file):
- `MODEL_NAME` (Required): The name of the model to be routed.
- `HF_TOKEN` (Required): The API key used for authentication. 

**Using an OpenAI-Compatible Interface:**
If you define `API_BASE_URL` alongside the required keys above, GhostQuery will preferentially use that specific endpoint via standard OpenAI client integration.

**Using Groq Fallback:**
If `API_BASE_URL` is omitted, the framework automatically instantiates Groq natively under-the-hood using your `HF_TOKEN` authentication.

