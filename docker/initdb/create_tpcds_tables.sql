-- Minimal TPC-DS-like table for local experiments
CREATE TABLE IF NOT EXISTS store_sales (
  ss_sold_date_sk BIGINT,
  ss_item_sk BIGINT,
  ss_sales_price NUMERIC(12,2),
  ss_quantity INTEGER,
  ss_net_paid NUMERIC(12,2)
);

INSERT INTO store_sales (ss_sold_date_sk, ss_item_sk, ss_sales_price, ss_quantity, ss_net_paid) VALUES
(20200101, 1001, 19.99, 1, 19.99),
(20200102, 1002, 9.50, 2, 19.00),
(20200103, 1001, 19.99, 3, 59.97)
ON CONFLICT DO NOTHING;
