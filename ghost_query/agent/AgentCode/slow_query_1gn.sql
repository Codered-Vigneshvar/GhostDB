SELECT 
    sale_id, 
    cust_id, 
    amount, 
    sale_time_str 
FROM sales 
WHERE sale_time_str > '2026-04-01 12:00:00' 
ORDER BY amount DESC, sale_id ASC 
LIMIT 1000;