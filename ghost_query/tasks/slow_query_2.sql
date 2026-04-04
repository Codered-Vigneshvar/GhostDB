-- Problem: Heavy Join + Aggregation + String Filtering
-- Goal: Filter sales FIRST, then run the join
SELECT 
    c.segment,
    COUNT(s.sale_id) as total_sales,
    SUM(s.amount) as total_revenue
FROM sales s
JOIN customers c ON s.cust_id = c.cust_id
WHERE CAST(s.sale_time_str AS TIMESTAMP) > '2026-04-01 08:00:00'
GROUP BY c.segment
ORDER BY total_revenue DESC;