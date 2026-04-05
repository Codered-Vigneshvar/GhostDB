select
  i.region_name,
  i.category_name,
  sum(i.quantity * i.unit_price * (1 - i.discount_pct)) as net_sales,
  sum(i.payment_amount) as payments,
  count(*) as row_count

from intermediate.int_order_line_enriched_bad i
group by
  i.region_name,
  i.category_name