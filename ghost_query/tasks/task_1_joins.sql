-- Task 1: Join Optimization Challenge
-- Unoptimized SQL:
SELECT * FROM Sales s1 JOIN Sales s2 ON s1.region_id = s2.region_id WHERE s1.region_id = 1;
