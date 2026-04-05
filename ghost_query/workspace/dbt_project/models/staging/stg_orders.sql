select
  order_id,
  customer_id_str,
  sales_rep_id,
  order_date,
  trim(order_status) as order_status
from raw.orders