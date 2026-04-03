# Building with GhostQuery: A Step-by-Step Guide

This document clearly outlines how to use the provided GhostQuery starter code to expand your DB World Simulation, construct an Agent to navigate it, and solidify the RL Environment.

---

## 1. DB World Simulation

The DB World Simulation acts as the "Physics Engine" of your benchmark. In GhostQuery, this is powered by an ultra-fast, in-memory DuckDB instance designed to spin up and tear down in milliseconds.

**How to expand and use it:**
*   **Data Generation (`scripts/seed_data.py`)**: This script constructs the core world state. To make the environment more challenging, increase `row_count` or introduce more complex relational structures (e.g., highly skewed datasets, large JSON blobs, deep hierarchies with explicit missing nulls).
*   **State Initialization (`server/sql_env.py`)**: The `reset()` method clears out the previous state, boots a fresh DuckDB memory block, and seeds the data. More importantly, this is where you define the **Baseline Query** (your problem statement). To test new capabilities, swap `self.baseline_query` with deliberately poorly-written SQL (such as heavy Cartesian joins or correlated subqueries).

---

## 2. Agent Integration

An agent is the decision-making entity (often an LLM or a specialized sub-network) that explores the DB World and attempts to optimize its state.

**How to expand and use it:**
*   **The Communication Contract (`models.py`)**: Your agent must digest `SQLObservation` (which contains the current latency, state parameters, and the all-important `query_plan_json`) and emit `SQLAction` (the rewritten, optimized query).
*   **Agent Execution Loop (`baseline.py`)**: To plug an LLM agent in, take inspiration from the `baseline.py` script. The agent executes `next_obs, reward, terminated, truncated, info = env.step(action)`. 
*   **Reasoning Mechanics**: Your agent should parse the `query_plan_json` coming from the `SQLObservation`. By identifying nodes like `SEQ_SCAN` (Full Table Scans) or large internal temp tables, the agent employs heuristics or Chain-of-Thought prompting to push down predicates and rewrite the JOIN schemas.

---

## 3. RL Environment Wrapper

The RL Environment securely wraps the simulation and enforces logical rules, scoring, and data-fidelity constraints so that a reinforcement learning algorithm can properly evaluate the agent.

**How to expand and use it:**
*   **The Reward Function (`server/sql_env.py`)**: Currently, the step method computes success as $R = \frac{T_{baseline} - T_{optimized}}{T_{baseline}}$. To refine the environment, consider expanding this function to deduct points for high memory overhead, repeated syntax failures, or excessively long planning times.
*   **The Grader (`grader.py`)**: The RL environment relies strictly on this verification layer to ensure agents aren't "cheating" by returning empty or incorrect outputs to fake a fast execution. The current codebase uses SHA-256 DataFrame hashing. If your DB World expands to hundreds of millions of rows, you should swap the Pandas sorting for a native `CHECKSUM()` DuckDB execution to maintain speed.
*   **Scaling & Deployment (`server/app.py` & `Dockerfile`)**: Because GhostQuery inherits from `openenv-core`, the environment is automatically exposed horizontally as a robust FastAPI microservice. An overlying RL orchestrator can manage episodes across hundreds of isolated Docker containers. Run `docker build -t ghostquery .` to containerize your RL node!
