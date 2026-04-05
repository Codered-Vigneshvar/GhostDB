select
  o.order_id,
  oi.order_line_id,
  o.customer_id_str,
  c.customer_name,
  r.region_name,
  p.sku,
  cat.category_name,
  oi.quantity,
  oi.unit_price,
  oi.discount_pct,

  inv.invoice_id,
  pay.payment_amount,
  s.shipment_id,
  s.ship_status

from staging.stg_orders o

join raw.order_items oi
  on o.order_id = oi.order_id

left join staging.stg_customers c
  on o.customer_id_str = cast(c.customer_id as varchar)

left join raw.regions r
  on c.region_id = r.region_id
left join raw.sales_reps sr
  on sr.region_id = r.region_id

left join raw.products p
  on oi.product_id = p.product_id

left join raw.categories cat
  on p.category_id = cat.category_id
left join raw.invoices inv
  on inv.order_id = o.order_id
left join raw.payments pay
  on pay.invoice_id = inv.invoice_id
left join raw.shipments s
  on s.order_id = o.order_id