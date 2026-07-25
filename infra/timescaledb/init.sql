-- ==========================================================================
-- Khalij DVC - TimescaleDB (سری زمانی موجودی، GPS، AIS، قیمت)
-- ==========================================================================

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- موجودی لحظه‌ای انبارها
CREATE TABLE IF NOT EXISTS inventory_ts (
    time            TIMESTAMPTZ NOT NULL,
    warehouse_code  VARCHAR(32) NOT NULL,
    product_grade   VARCHAR(32) NOT NULL,
    quantity_tons   DOUBLE PRECISION NOT NULL,
    fill_rate_pct   DOUBLE PRECISION
);

SELECT create_hypertable('inventory_ts', 'time', if_not_exists => TRUE);

-- موقعیت محموله‌ها (GPS / AIS)
CREATE TABLE IF NOT EXISTS shipment_positions_ts (
    time            TIMESTAMPTZ NOT NULL,
    shipment_number VARCHAR(64) NOT NULL,
    latitude        DOUBLE PRECISION NOT NULL,
    longitude       DOUBLE PRECISION NOT NULL,
    speed_knots     DOUBLE PRECISION,
    heading_deg     DOUBLE PRECISION,
    source          VARCHAR(16) NOT NULL DEFAULT 'GPS'  -- GPS | AIS
);

SELECT create_hypertable('shipment_positions_ts', 'time', if_not_exists => TRUE);

-- قیمت‌های بازار و خوراک
CREATE TABLE IF NOT EXISTS market_prices_ts (
    time            TIMESTAMPTZ NOT NULL,
    oil_price_usd_bbl DOUBLE PRECISION,
    price_hdpe_usd_ton DOUBLE PRECISION,
    price_pp_usd_ton DOUBLE PRECISION,
    feedstock_price_usd_ton DOUBLE PRECISION,
    fx_usd_irr      DOUBLE PRECISION
);

SELECT create_hypertable('market_prices_ts', 'time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_inventory_ts_wh ON inventory_ts (warehouse_code, time DESC);
CREATE INDEX IF NOT EXISTS idx_shipment_pos_num ON shipment_positions_ts (shipment_number, time DESC);
