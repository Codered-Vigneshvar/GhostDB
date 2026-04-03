-- FILE: tasks/heavy_disaster.sql
-- WARNING: This simulates a "Runaway Query" in Snowflake.
-- The AI Agent's goal is to find the "Fan-out" and fix the Join logic.

SELECT 
    s.sale_id,
    c.segment,
    s.amount * m.trend_index as adjusted_revenue
FROM sales s
JOIN customers c ON s.cust_id = c.cust_id
JOIN market_trends m ON c.segment = m.segment
WHERE CAST(s.sale_time_str AS TIMESTAMP) > '2026-04-01 10:00:00'
  AND m.trend_index > 0.5
ORDER BY adjusted_revenue DESC
LIMIT 100;