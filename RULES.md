# 🏛️ GHOSTQUERY PROJECT: CORE OPERATIONAL PROTOCOL

## 1. ARCHITECTURAL MANDATE (DECOUPLED SYSTEMS)
- **Architecture:** Must follow a Client-Server (Headless) model.
- **The World (Server):** A FastAPI microservice (`app.py`) that manages a stateful DuckDB in-memory session.
- **The Agent (Client):** A standalone script (`agent.py`) that drives the environment via HTTP requests.
- **Strict Rule:** No manual file-sharing or shared memory. The Agent communicates ONLY via the `/reset` and `/step` API endpoints.

## 2. THE EPISODE LIFECYCLE (GYMNASIUM STANDARDS)
The environment logic must strictly implement the following Gymnasium-style lifecycle:

### **A. Phase 1: Reset (`POST /reset`)**
- **Action:** Wipes the DuckDB session and reloads tables from `/data/*.parquet`.
- **Baseline:** Pick one random `.sql` task from `/tasks`, run it ONCE, and record the `baseline_latency`.
- **Observation:** Return a JSON containing:
  - `original_sql`: The messy SQL string.
  - `baseline_latency`: Float value in milliseconds.
  - `query_plan`: The initial execution tree (EXPLAIN output).

### **B. Phase 2: Step (`POST /step`)**
- **Input:** Takes an `optimized_sql` string from the Agent.
- **Physics Engine:** Executes the query in DuckDB.
- **Integrity Check:** MUST run a SHA-256 hash comparison between the baseline result set and the new result set.
  - **Match:** Calculate reward.
  - **Mismatch:** Return `reward = -1.0` (Hard Failure/Data Corruption).
- **Reward Formula:** $R = (T_{baseline} - T_{new}) / T_{baseline}$.
- **Return:** New `latency`, `reward`, `is_valid`, and the new `query_plan`.

## 3. ARTIFACT GENERATION (THE RESEARCH REPORT)
Upon completion of a task, the Agent must automatically generate a `SUMMARY.md` file.
- **Side-by-Side Plan:** Display original vs. optimized DuckDB query plans.
- **Metrics Table:** Show `Original Time`, `Optimized Time`, and `% Speedup`.
- **Agent Reasoning:** Include Gemini's short explanation for the change (e.g., "Eliminated Full Table Scan by indexing column X").

## 4. COMPLIANCE & VALIDATION
- **CLI Standard:** Code must always be verified by running `openenv validate .` in the terminal.
- **Hugging Face Compatibility:** The World must be containerized via the `Dockerfile` provided, exposing Port 8000.
- **Concurrency:** `SUPPORTS_CONCURRENT_SESSIONS` should be False for Round 1 to ensure dedicated DuckDB instances.

## 5. REPOSITORY STRUCTURE
- `/environment`: The "Physics" (Teammate's logic).
- `/agent`: The "Brain" (Your Gemini logic).
- `/tasks`: Folder for raw `.sql` files.
- `models.py`: Typed Pydantic schemas (Action/Observation/State).