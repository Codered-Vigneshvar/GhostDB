-- Task 2: CTE vs Subquery Optimization
-- Unoptimized SQL:
SELECT * FROM (SELECT region_id, SUM(amount) FROM Sales GROUP BY region_id) t WHERE t.region_id = 2;
