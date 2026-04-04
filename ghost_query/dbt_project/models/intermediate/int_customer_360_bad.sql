select
  c.customer_id,
  c.customer_name,
  r.region_name,

  count(distinct o.order_id) as order_count,

  sum(oi.quantity * oi.unit_price * (1 - oi.discount_pct)) as gross_sales,
  sum(pay.payment_amount) as total_payments,

  count(s.shipment_id) as shipment_events

from staging.stg_customers c

left join raw.regions r
  on c.region_id = r.region_id

left join staging.stg_orders o
  on cast(c.customer_id as varchar) = o.customer_id_str

left join raw.order_items oi
  on oi.order_id = o.order_id

left join raw.invoices inv
  on inv.order_id = o.order_id

left join raw.payments pay
  on pay.invoice_id = inv.invoice_id

left join raw.shipments s
  on s.order_id = o.order_id

group by
  c.customer_id,
  c.customer_name,
  r.region_name