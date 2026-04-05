-- ======================
-- DUCKDB: RAW LAYER SETUP (FIXED)
-- ======================
CREATE SCHEMA IF NOT EXISTS raw;

-- =====================================================
-- REGIONS (5M)
-- =====================================================
CREATE OR REPLACE TABLE raw.regions AS
SELECT
  i AS region_id,
  'R' || lpad(i::VARCHAR, 6, '0') AS region_code,
  CASE WHEN i % 50 = 0 THEN NULL ELSE 'Region ' || (i % 5000) END AS region_name,
  CASE WHEN i % 97 = 0 THEN 'XX' ELSE 'US' END AS country_code
FROM range(1, 5000000 + 1) t(i);

-- =====================================================
-- SALES_REPS (5M)
-- =====================================================
CREATE OR REPLACE TABLE raw.sales_reps AS
SELECT
  i AS sales_rep_id,
  CASE WHEN i % 1000 = 0 THEN NULL ELSE 'SR' || lpad(i::VARCHAR, 8, '0') END AS sales_rep_code,
  (i % 5000000) + 1 AS region_id,
  CASE WHEN i % 123 = 0 THEN 'INACTIVE' ELSE 'ACTIVE' END AS status
FROM range(1, 5000000 + 1) t(i);

-- =====================================================
-- CATEGORIES (5M)
-- =====================================================
CREATE OR REPLACE TABLE raw.categories AS
SELECT
  i AS category_id,
  'CAT' || lpad(i::VARCHAR, 7, '0') AS category_code,
  CASE WHEN i % 777 = 0 THEN '' ELSE 'Category ' || (i % 100000) END AS category_name
FROM range(1, 5000000 + 1) t(i);

-- =====================================================
-- PRODUCTS (5M)
-- =====================================================
CREATE OR REPLACE TABLE raw.products AS
SELECT
  i AS product_id,
  (i % 5000000) + 1 AS category_id,
  'SKU' || lpad(i::VARCHAR, 10, '0') AS sku,
  CASE WHEN i % 500 = 0 THEN NULL ELSE 'Product ' || (i % 500000) END AS product_name,
  CASE
    WHEN i % 250 = 0 THEN 'FREE'
    ELSE CAST((i % 20000) / 100.0 AS VARCHAR)
  END AS list_price_str
FROM range(1, 5000000 + 1) t(i);

-- =====================================================
-- CUSTOMERS (5M + DUPLICATES)
-- =====================================================
CREATE OR REPLACE TABLE raw.customers AS
WITH base AS (
  SELECT
    i AS customer_id,
    'C' || lpad(i::VARCHAR, 10, '0') AS customer_nbr,
    (i % 5000000) + 1 AS region_id,
    CASE WHEN i % 1000 = 0 THEN NULL ELSE 'Customer ' || (i % 2000000) END AS customer_name,
    CASE WHEN i % 333 = 0 THEN 'UNKNOWN' ELSE 'RETAIL' END AS customer_type
  FROM range(1, 5000000 + 1) t(i)
)
SELECT * FROM base
UNION ALL
SELECT * FROM base WHERE customer_id % 1000 = 0;

-- =====================================================
-- CUSTOMER_ADDRESSES (5M)
-- =====================================================
CREATE OR REPLACE TABLE raw.customer_addresses AS
SELECT
  i AS address_id,
  CASE
    WHEN i % 200 = 0 THEN 5000000 + (i % 100000)
    ELSE (i % 5000000) + 1
  END AS customer_id,
  CASE WHEN i % 150 = 0 THEN NULL ELSE 'Street ' || (i % 5000000) END AS street,
  'City ' || (i % 100000) AS city,
  CASE WHEN i % 500 = 0 THEN '??' ELSE 'TN' END AS state,
  lpad(CAST(i % 999999 AS VARCHAR), 6, '0') AS zip
FROM range(1, 5000000 + 1) t(i);

-- =====================================================
-- ORDERS (15M) ✅ FIXED DATE
-- =====================================================
CREATE OR REPLACE TABLE raw.orders AS
SELECT
  i AS order_id,
  CASE
    WHEN i % 120 = 0 THEN 'X' || CAST((i % 5000000) + 1 AS VARCHAR)
    ELSE CAST((i % 5000000) + 1 AS VARCHAR)
  END AS customer_id_str,
  (i % 5000000) + 1 AS sales_rep_id,
  current_date - (i % 3650)::INTEGER AS order_date,
  CASE
    WHEN i % 90 = 0 THEN 'CANCELLED'
    WHEN i % 91 = 0 THEN 'CANCELLED '
    ELSE 'COMPLETE'
  END AS order_status
FROM range(1, 15000000 + 1) t(i);

-- =====================================================
-- ORDER_ITEMS (15M)
-- =====================================================
CREATE OR REPLACE TABLE raw.order_items AS
SELECT
  i AS order_line_id,
  (i % 15000000) + 1 AS order_id,
  (i % 5000000) + 1 AS product_id,
  CASE WHEN i % 250 = 0 THEN -1 ELSE (i % 20) + 1 END AS quantity,
  (i % 20000) / 100.0 AS unit_price,
  CASE WHEN i % 300 = 0 THEN 2.5 ELSE (i % 500) / 100.0 END AS discount_pct
FROM range(1, 15000000 + 1) t(i);

-- =====================================================
-- SHIPMENTS (15M) ✅ FIXED DATE
-- =====================================================
CREATE OR REPLACE TABLE raw.shipments AS
SELECT
  i AS shipment_id,
  (i % 15000000) + 1 AS order_id,
  CASE WHEN i % 100 = 0 THEN NULL ELSE (i % 15000000) + 1 END AS order_line_id,
  current_date
    - (i % 3650)::INTEGER
    + (i % 30)::INTEGER AS ship_date,
  CASE WHEN i % 500 = 0 THEN 'LOST' ELSE 'SHIPPED' END AS ship_status
FROM range(1, 15000000 + 1) t(i);

-- =====================================================
-- INVOICES (15M) ✅ FIXED DATE
-- =====================================================
CREATE OR REPLACE TABLE raw.invoices AS
SELECT
  i AS invoice_id,
  (i % 15000000) + 1 AS order_id,
  current_date
    - (i % 3650)::INTEGER
    + (i % 15)::INTEGER AS invoice_date,
  (i % 100000) / 100.0 AS tax_amount,
  (i % 500000) / 100.0 AS shipping_amount
FROM range(1, 15000000 + 1) t(i);

-- =====================================================
-- PAYMENTS (15M) ✅ FIXED DATE
-- =====================================================
CREATE OR REPLACE TABLE raw.payments AS
SELECT
  i AS payment_id,
  CASE
    WHEN i % 400 = 0 THEN 15000000 + (i % 10000)
    ELSE (i % 15000000) + 1
  END AS invoice_id,
  current_date
    - (i % 3650)::INTEGER
    + (i % 60)::INTEGER AS payment_date,
  CASE WHEN i % 200 = 0 THEN -10.0 ELSE (i % 200000) / 100.0 END AS payment_amount,
  CASE WHEN i % 333 = 0 THEN 'CRYPTO' ELSE 'CARD' END AS payment_method
FROM range(1, 15000000 + 1) t(i);