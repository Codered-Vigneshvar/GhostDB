-- Problem: String casting in WHERE clause prevents pruning
-- Goal: Fix the CAST and remove unnecessary columns
SELECT 
    * FROM sales 
WHERE CAST(sale_time_str AS TIMESTAMP) > '2026-04-01 12:00:00' 
ORDER BY amount DESC 
LIMIT 1000;