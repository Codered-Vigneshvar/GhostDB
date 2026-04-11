# GhostQuery — How It Works

## What Is It?

GhostQuery is an adversarial multi-agent simulation. An **AttackerAgent** secretly corrupts a live data pipeline, and a **DefenderAgent** must detect and repair the damage. An **EvaluatorAgent** then scores both sides. The whole thing runs as an HTTP server that the Meta OpenEnv hackathon can call to run benchmark episodes.

---

## The Full Flow

```
POST /reset
    → Reset workspace to clean state
    → AttackerAgent reads tables, injects corruption, persists to disk
    → Return: corrupted observation (latency, table stats, round_id)

POST /step  (called repeatedly by the evaluator/agent)
    → Execute a repair SQL action against the live DB
    → Check if data integrity is restored (null counts, row counts match baseline)
    → Return: reward (0.0–1.0), done flag, reason

GET /state
    → Return: current step count, pipeline latency, query latency
```

---

## The Three Agents

### 1. AttackerAgent (`ghost_query/agent/attacker_agent.py`)

**What it does:** Reads the live workspace tables, uses an LLM to plan a targeted SQL mutation that causes silent data corruption, validates it actually changed something, then persists the damage.

**Step by step:**
1. Queries row counts on `sales`, `customers`, `market_trends` to understand the environment
2. Sends that context to `AttackerPlanner` (LLM call via Groq) — asks it to pick a table, a column, and write a malicious SQL UPDATE
3. Runs the SQL on the live DuckDB connection
4. Captures before/after null counts and cardinality — if nothing changed, retries up to 3 times
5. Once a measurable delta is confirmed, calls `COPY table TO parquet` to persist the corruption to disk — this is critical, because the DB is in-memory and gets reloaded on every pipeline run
6. Saves the "attack dossier" (strategy, SQL used, target table/column) to `metadata/attack_truth/`

**Fallback:** If all 3 attempts fail to produce a measurable change, it falls back to a hardcoded null injection: `UPDATE sales SET amount = NULL WHERE random() < 0.05`

**Attack types the LLM can choose:**
- Null injection (set ~5% of `sales.amount` to NULL)
- Duplicate skew (insert duplicate customer IDs)
- Date drift (shift `order_date` to cause silent join failures)

---

### 2. DefenderAgent (`ghost_query/agent/defender_agent.py`)

**What it does:** Loads the attack dossier and baseline metrics, then runs an iterative ReAct loop — each iteration: observe current state → ask LLM what to fix → apply the fix → verify if integrity is restored.

**Step by step:**
1. Loads `metadata/baseline_metrics.json` (the clean SHA-256 hash of table stats before attack)
2. Loads `metadata/attack_truth/round_X.json` (the attacker's dossier)
3. Runs a **programmatic pre-check first**: if the current results_hash already matches baseline (within 50% latency jitter), it exits immediately — no LLM calls wasted
4. If corruption is detected, enters the agentic loop (max 5 iterations):
   - Builds a context string describing the anomaly (null counts, latency delta, attack hint)
   - Sends context to `DefenderPlanner` (LLM call) — asks for a file to edit and new SQL content
   - The LLM targets `workspace/fix_nulls.sql` — a repair hook that gets auto-applied on every DB reload
   - Writes the SQL to `fix_nulls.sql`, reloads the pipeline, checks if hash matches baseline
   - If yes: done. If no: backs up the file, logs the failure, tries again
5. Saves repair dossier to `metadata/repair_truth/`

**The repair hook mechanism:** `fix_nulls.sql` is automatically executed by the DB engine every time it loads parquet files. So a fix like:
```sql
UPDATE sales SET amount = 100.0 WHERE amount IS NULL;
```
...will survive any future reload, making the repair durable.

---

### 3. EvaluatorAgent (`ghost_query/agent/evaluator_agent.py`)

**What it does:** Loads both the attack dossier and the defender's repair report, then computes RL scores for both sides.

**Scoring breakdown:**

| Component | Points | How it's measured |
|---|---|---|
| Detection | +0.2 | Did the defender's reasoning mention the right keywords (null/duplicate/date) AND the right table? |
| Fix | +0.5 | Did `repair_truth.success` come back True? |
| Efficiency | +0.2 | `0.2 / iterations` — fewer iterations = higher score |
| Consistency | +0.1 | Did the defender both detect AND fix? |
| **Max total** | **1.0** | |

**Attacker scoring:**

| Outcome | Score |
|---|---|
| No measurable attack | 0.0 |
| Defender fixed in 1 iteration | 0.0 (too easy) |
| Fixed in 2–3 iterations | 0.5 |
| Took 4–5 iterations or failed | 1.0 (attacker wins) |

---

## The Data Pipeline

The underlying "data pipeline" the agents fight over is a mini dbt-style SQL pipeline running on DuckDB:

```
raw.sales + raw.customers + raw.market_trends   ← Parquet files
    ↓
stg_sales, stg_customers, stg_market_trends     ← Staging models (clean/type-cast)
    ↓
int_order_line_enriched                         ← Joins sales + customers
    ↓
mart_sales_billing_report                       ← Final output (revenue, totals)
```

The `results_hash` is a SHA-256 over the row counts, null counts, and cardinality of every column in every table. If the attacker changes any of these, the hash breaks. The defender's job is to restore it.

---

## Environment Variables

| Variable | What it does |
|---|---|
| `HF_TOKEN` | Your Groq (or HuggingFace) API key — required to run the LLM agents |
| `MODEL_NAME` | LLM model (default: `llama-3.3-70b-versatile`) |
| `API_BASE_URL` | OpenAI-compatible endpoint (default: `https://api.groq.com/openai/v1`) |

---

## Key Files

| File | Role |
|---|---|
| `ghost_query/agent/attacker_agent.py` | Generates and validates the attack |
| `ghost_query/agent/attacker_planner.py` | LLM ReAct loop for attack planning |
| `ghost_query/agent/defender_agent.py` | Iterative repair loop |
| `ghost_query/agent/defender_planner.py` | Single-shot LLM edit decision |
| `ghost_query/agent/defender_context.py` | Builds the LLM context string for the defender |
| `ghost_query/agent/evaluator_agent.py` | RL scoring |
| `ghost_query/agent/llm_client.py` | OpenAI-compatible client with 429 backoff |
| `ghost_query/environment/sql_env.py` | OpenEnv Environment — wires reset/step/state |
| `ghost_query/environment/engine.py` | DuckDB wrapper — loads parquets, runs fix_nulls.sql |
| `ghost_query/environment/baseline_runner.py` | Runs pipeline, computes results_hash |
| `ghost_query/environment/reset_manager.py` | Copies baseline/ → workspace/ at start of each round |
| `ghost_query/api/openenv_app.py` | FastAPI server entry point |
| `ghost_query/workspace/fix_nulls.sql` | Repair hook written by the DefenderAgent |
| `ghost_query/baseline/data/*.parquet` | Clean reference data (tracked in git) |
| `inference.py` | Benchmark runner — outputs structured [START]/[STEP]/[END] logs |

---

## Reward Function (in `/step`)

```
If data integrity NOT restored:   reward = 0.0
If data integrity restored:       reward = clamp(latency_reduction% / 100 + 0.5, 0.0, 1.0)

done = True  when:  integrity restored  AND  pipeline latency ≤ 1.2× baseline
```

A perfect fix that also makes the pipeline faster than baseline scores close to 1.0.
