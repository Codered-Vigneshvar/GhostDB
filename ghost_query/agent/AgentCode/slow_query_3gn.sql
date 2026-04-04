SELECT 
    s.sale_id,
    c.segment,
    s.amount * m.trend_index as adjusted_revenue
FROM (
    SELECT sale_id, cust_id, amount, sale_time_str
    FROM sales
    WHERE sale_time_str > '2026-04-01 10:00:00'
) s
JOIN customers c ON s.cust_id = c.cust_id
JOIN market_trends m ON c.segment = m.segment
WHERE m.trend_index > 0.5
ORDER BY s.amount * m.trend_index DESC
LIMIT 100;