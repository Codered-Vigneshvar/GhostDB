-- Repair for manual_null_v3
-- Fixing NULL values in sales.amount by defaulting to 0
UPDATE sales SET amount = 0 WHERE amount IS NULL;
