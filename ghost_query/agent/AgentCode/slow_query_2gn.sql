WITH filtered_sales AS (
  SELECT sale_id, cust_id, amount
  FROM sales
  WHERE sale_time_str >= '2026-04-01 08:00:00'
),
joined_result AS (
  SELECT c.segment, COUNT(fs.sale_id) as total_sales, SUM(fs.amount) as total_revenue
  FROM filtered_sales fs
  JOIN customers c ON fs.cust_id = c.cust_id
  GROUP BY c.segment
)
SELECT segment, total_sales, total_revenue
FROM joined_result
ORDER BY total_revenue DESC;