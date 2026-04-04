# GHOSTQUERY: Data Engineering Expert Rules
# Purpose: Ensure high-fidelity SQL optimization and data integrity

## 1. DUCKDB SPECIALIZATION
- Always use `EXPLAIN ANALYZE` to capture actual execution metrics, not just timestamps.
- Use PARQUET files for large dummy datasets to simulate "Big Data" columnar storage.
- Ensure the DB connection is thread-safe if the environment is accessed concurrently.

## 2. THE "SCIENTIST" CORRECTNESS CHECK
- Before calculating rewards, MUST run a Checksum/Hash on the result set of the agent's SQL.
- If `hash(agent_results) != hash(baseline_results)`, the agent has "corrupted" the data. 
- ACTION: Immediate Done = True, Reward = -2.0. (Correctness is non-negotiable).

## 3. SQL REFACTORING FOCUS
- The agent should prioritize: 
    1. Predicate Pushdown (WHERE clauses).
    2. Column Pruning (Removing SELECT *).
    3. Join Reordering or Indexing suggestions.
- Do not reward "cosmetic" changes like capitalization or indentation.

## 4. FEEDBACK FIDELITY
- The `Observation` must include the "Query Plan" as a string so the agent can "reason" about why it was slow (e.g., finding a Sequential Scan).