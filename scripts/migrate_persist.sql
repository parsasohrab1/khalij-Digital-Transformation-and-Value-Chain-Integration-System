-- Apply on existing Postgres volumes (fresh installs already have these via init.sql)
ALTER TABLE orders ADD COLUMN IF NOT EXISTS product_grade VARCHAR(32);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS allocated_warehouse_code VARCHAR(32);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS destination VARCHAR(256);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(32) DEFAULT 'unpaid';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(64);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipment_number VARCHAR(64);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}';

ALTER TABLE invoices ADD COLUMN IF NOT EXISTS order_number VARCHAR(64);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}';

ALTER TABLE shipments ADD COLUMN IF NOT EXISTS order_number VARCHAR(64);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS product_grade VARCHAR(32);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS quantity_tons DOUBLE PRECISION;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS value_usd DOUBLE PRECISION;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}';
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS message_ar TEXT;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS subsidiary_code VARCHAR(32);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_by_name VARCHAR(128);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS payload_json JSONB NOT NULL DEFAULT '{}';

CREATE TABLE IF NOT EXISTS inventory_levels (
    warehouse_code  VARCHAR(32) NOT NULL,
    product_grade   VARCHAR(32) NOT NULL,
    quantity_tons   DOUBLE PRECISION NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (warehouse_code, product_grade)
);

CREATE TABLE IF NOT EXISTS payments (
    id              BIGSERIAL PRIMARY KEY,
    payment_number  VARCHAR(64) UNIQUE NOT NULL,
    invoice_number  VARCHAR(64) NOT NULL,
    amount_usd      DOUBLE PRECISION NOT NULL,
    method          VARCHAR(32) NOT NULL DEFAULT 'wire',
    reference       VARCHAR(128),
    payload_json    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
