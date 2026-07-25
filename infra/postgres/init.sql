-- ==========================================================================
-- Khalij DVC - Schema اولیه PostgreSQL
-- Data Mesh: مالکیت غیرمتمرکز داده به ازای هر شرکت تابعه (نوآوری ثبت اختراع)
-- ==========================================================================

SELECT 'CREATE DATABASE mlflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'mlflow')
\gexec

-- ---------------------------------------------------------------------
-- شرکت‌های تابعه هلدینگ (دامنه‌های Data Mesh)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS subsidiaries (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(32) UNIQUE NOT NULL,  -- e.g. NPC, BIPC, PIDMCO
    name_fa         VARCHAR(128) NOT NULL,
    name_en         VARCHAR(128) NOT NULL,
    name_ar         VARCHAR(128),
    domain_owner    VARCHAR(128) NOT NULL,        -- مالک دامنه داده (Data Mesh)
    kafka_topic     VARCHAR(128) NOT NULL,        -- topic اختصاصی شرکت تابعه
    region          VARCHAR(64),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- کاربران و RBAC (NFR-SEC-02)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    employee_code   VARCHAR(32) UNIQUE NOT NULL,
    full_name       VARCHAR(128) NOT NULL,
    password_hash   VARCHAR(256) NOT NULL,
    otp_secret      VARCHAR(64),
    role            VARCHAR(32) NOT NULL DEFAULT 'operator',
    -- roles: operator | supervisor | logistics | sales | analyst | admin | executive
    subsidiary_id   INTEGER REFERENCES subsidiaries(id),
    locale          VARCHAR(8) NOT NULL DEFAULT 'fa',  -- fa | en | ar (R-GEN-04)
    two_factor_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- کاتالوگ محصول و استانداردسازی شناسه (FR-DATA-03)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    internal_code   VARCHAR(64) UNIQUE NOT NULL,
    hs_code         VARCHAR(16),                  -- کد HS بین‌المللی
    grade           VARCHAR(32) NOT NULL,         -- HDPE | LDPE | LLDPE | PP | PET
    name_fa         VARCHAR(128) NOT NULL,
    name_en         VARCHAR(128) NOT NULL,
    uom             VARCHAR(16) NOT NULL DEFAULT 'ton',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- انبارها
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS warehouses (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(32) UNIQUE NOT NULL,
    name_fa         VARCHAR(128) NOT NULL,
    name_en         VARCHAR(128) NOT NULL,
    city            VARCHAR(64) NOT NULL,
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION,
    capacity_tons   DOUBLE PRECISION NOT NULL,
    subsidiary_id   INTEGER REFERENCES subsidiaries(id),
    port_code       VARCHAR(32),                  -- اتصال به بنادر ایران
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- واحدهای تولیدی (برای تخصیص خوراک - FR-ML-02)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS production_units (
    id              SERIAL PRIMARY KEY,
    code            VARCHAR(32) UNIQUE NOT NULL,
    name_fa         VARCHAR(128) NOT NULL,
    subsidiary_id   INTEGER REFERENCES subsidiaries(id),
    feedstock_type  VARCHAR(32) NOT NULL DEFAULT 'ethylene',
    max_feed_tons_day DOUBLE PRECISION NOT NULL,
    margin_per_ton_usd DOUBLE PRECISION NOT NULL DEFAULT 200,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- سفارشات (Order-to-Cash - FR-ORDER-01)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id              BIGSERIAL PRIMARY KEY,
    order_number    VARCHAR(64) UNIQUE NOT NULL,
    channel         VARCHAR(32) NOT NULL,         -- online | contract | auction
    product_id      INTEGER REFERENCES products(id),
    quantity_tons   DOUBLE PRECISION NOT NULL,
    value_usd       DOUBLE PRECISION NOT NULL,
    customer_name   VARCHAR(256),
    customer_country VARCHAR(64),
    status          VARCHAR(32) NOT NULL DEFAULT 'pending',
    -- pending | allocated | invoiced | shipped | delivered | cancelled
    allocated_warehouse_id INTEGER REFERENCES warehouses(id),
    subsidiary_id   INTEGER REFERENCES subsidiaries(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orders_status ON orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders (created_at DESC);

-- ---------------------------------------------------------------------
-- فاکتورها (FR-ORDER-03)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT REFERENCES orders(id),
    invoice_number  VARCHAR(64) UNIQUE NOT NULL,
    amount_usd      DOUBLE PRECISION NOT NULL,
    currency        VARCHAR(8) NOT NULL DEFAULT 'USD',
    status          VARCHAR(32) NOT NULL DEFAULT 'issued',
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    paid_at         TIMESTAMPTZ
);

-- ---------------------------------------------------------------------
-- محموله‌ها و ردیابی (FR-LOG-01 / بومی‌سازی ایران)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS shipments (
    id              BIGSERIAL PRIMARY KEY,
    shipment_number VARCHAR(64) UNIQUE NOT NULL,
    order_id        BIGINT REFERENCES orders(id),
    mode            VARCHAR(16) NOT NULL,         -- sea | road | rail
    origin_port     VARCHAR(64),                  -- BandarAbbas | Assaluyeh | Bushehr | ImamKhomeini
    destination     VARCHAR(256),
    customs_declaration VARCHAR(64),              -- شماره اظهارنامه گمرکی ایران
    ais_mmsi        VARCHAR(32),                  -- شناسه AIS کشتی
    gps_device_id   VARCHAR(64),
    eta_days        DOUBLE PRECISION,
    status          VARCHAR(32) NOT NULL DEFAULT 'planned',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments (status);

-- ---------------------------------------------------------------------
-- هشدارهای هوشمند (FR-BI-03)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id              BIGSERIAL PRIMARY KEY,
    alert_type      VARCHAR(64) NOT NULL,         -- production | sales | budget | logistics | inventory
    severity        VARCHAR(16) NOT NULL,         -- info | warning | critical
    message_fa      TEXT NOT NULL,
    message_en      TEXT,
    subsidiary_id   INTEGER REFERENCES subsidiaries(id),
    metric_name     VARCHAR(64),
    metric_value    DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    raised_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_alerts_raised_at ON alerts (raised_at DESC);

-- ---------------------------------------------------------------------
-- نتایج بهینه‌سازی یکپارچه (قابلیت ثبت اختراع FR-ML-01/02)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS optimization_runs (
    id              BIGSERIAL PRIMARY KEY,
    run_type        VARCHAR(64) NOT NULL,         -- demand_forecast | feedstock_lp | trading | integrated
    objective_value DOUBLE PRECISION,             -- حاشیه سود کل هلدینگ
    horizon_days    INTEGER,
    model_run_id    VARCHAR(64),                  -- MLflow run id
    payload_json    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- نسب‌شناسی داده / Data Lineage سبک (جایگزین اولیه Apache Atlas)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_lineage (
    id              BIGSERIAL PRIMARY KEY,
    source_system   VARCHAR(128) NOT NULL,        -- Oracle | SQLServer | PostgreSQL | SAP | ERP
    source_entity   VARCHAR(256) NOT NULL,
    domain_code     VARCHAR(32) NOT NULL,         -- کد شرکت تابعه مالک
    target_topic    VARCHAR(128),
    target_table    VARCHAR(128),
    transform_note  TEXT,
    records_count   INTEGER DEFAULT 0,
    schema_version  VARCHAR(16) DEFAULT '1.0.0',
    payload_json    JSONB NOT NULL DEFAULT '{}',
    recorded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- رجیستری کانکتورهای OLTP / ERP (فاز ۱ — Data Mesh)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_connectors (
    id              SERIAL PRIMARY KEY,
    connector_key   VARCHAR(64) UNIQUE NOT NULL,
    source_system   VARCHAR(32) NOT NULL,         -- Oracle | SQLServer | PostgreSQL | SAP | ERP
    subsidiary_code VARCHAR(32) NOT NULL,
    connection_uri  TEXT NOT NULL,
    source_entity   VARCHAR(256) NOT NULL,
    kafka_topic     VARCHAR(128) NOT NULL,
    domain_owner    VARCHAR(128) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_ingest_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS model_registry_meta (
    id              SERIAL PRIMARY KEY,
    model_name      VARCHAR(64) NOT NULL,
    model_version   VARCHAR(32) NOT NULL,
    mlflow_run_id   VARCHAR(64),
    metrics_json    JSONB NOT NULL DEFAULT '{}',
    is_production   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- داده اولیه: شرکت‌های تابعه (دامنه‌های Data Mesh)
-- ---------------------------------------------------------------------
INSERT INTO subsidiaries (code, name_fa, name_en, name_ar, domain_owner, kafka_topic, region) VALUES
    ('NPC',   'شرکت ملی صنایع پتروشیمی', 'National Petrochemical Company', 'الشركة الوطنية للبتروكيماويات', 'npc-data-owner', 'dvc.subsidiary.npc', 'Tehran'),
    ('BIPC',  'پتروشیمی بندرامام', 'Bandar Imam Petrochemical', 'بتروكيماويات بندر إمام', 'bipc-data-owner', 'dvc.subsidiary.bipc', 'Khuzestan'),
    ('PIDMCO','پتروشیمی پردیس', 'Pardis Petrochemical', 'بتروكيماويات بارديس', 'pidmco-data-owner', 'dvc.subsidiary.pidmco', 'Assaluyeh'),
    ('ARPC',  'پتروشیمی آرین', 'Aryan Petrochemical', 'بتروكيماويات آريان', 'arpc-data-owner', 'dvc.subsidiary.arpc', 'Assaluyeh')
ON CONFLICT (code) DO NOTHING;

INSERT INTO products (internal_code, hs_code, grade, name_fa, name_en) VALUES
    ('POLY-HDPE-01', '390120', 'HDPE',  'پلی‌اتیلن سنگین', 'High-Density Polyethylene'),
    ('POLY-LDPE-01', '390110', 'LDPE',  'پلی‌اتیلن سبک', 'Low-Density Polyethylene'),
    ('POLY-LLDPE-01','390190', 'LLDPE', 'پلی‌اتیلن سبک خطی', 'Linear Low-Density Polyethylene'),
    ('POLY-PP-01',   '390210', 'PP',    'پلی‌پروپیلن', 'Polypropylene'),
    ('POLY-PET-01',  '390760', 'PET',   'پلی‌اتیلن ترفتالات', 'Polyethylene Terephthalate')
ON CONFLICT (internal_code) DO NOTHING;

INSERT INTO warehouses (code, name_fa, name_en, city, latitude, longitude, capacity_tons, subsidiary_id, port_code)
SELECT v.code, v.name_fa, v.name_en, v.city, v.lat, v.lon, v.cap, s.id, v.port
FROM (VALUES
    ('WH-BND', 'انبار بندرعباس', 'Bandar Abbas Warehouse', 'Bandar Abbas', 27.1832, 56.2666, 8000::float, 'BIPC', 'IRBND'),
    ('WH-THR', 'انبار تهران', 'Tehran Warehouse', 'Tehran', 35.6892, 51.3890, 6000::float, 'NPC', NULL),
    ('WH-ASL', 'انبار عسلویه', 'Assaluyeh Warehouse', 'Assaluyeh', 27.4761, 52.6070, 12000::float, 'PIDMCO', 'IRASL')
) AS v(code, name_fa, name_en, city, lat, lon, cap, sub_code, port)
JOIN subsidiaries s ON s.code = v.sub_code
ON CONFLICT (code) DO NOTHING;

INSERT INTO production_units (code, name_fa, subsidiary_id, feedstock_type, max_feed_tons_day, margin_per_ton_usd)
SELECT v.code, v.name_fa, s.id, v.feed, v.max_feed, v.margin
FROM (VALUES
    ('PU-BIPC-1', 'واحد الفین بندرامام ۱', 'BIPC', 'ethylene', 1200::float, 220::float),
    ('PU-PID-1',  'واحد اوره پردیس ۱', 'PIDMCO', 'methane', 2000::float, 180::float),
    ('PU-ARPC-1', 'واحد پلیمر آرین ۱', 'ARPC', 'ethylene', 900::float, 250::float),
    ('PU-NPC-1',  'واحد پلی‌پروپیلن مرکزی', 'NPC', 'propylene', 800::float, 210::float)
) AS v(code, name_fa, sub_code, feed, max_feed, margin)
JOIN subsidiaries s ON s.code = v.sub_code
ON CONFLICT (code) DO NOTHING;

-- کاربر دمو: رمز ChangeMe123!  /  OTP secret برای تست
INSERT INTO users (employee_code, full_name, password_hash, otp_secret, role, locale)
VALUES (
    'demo-admin',
    'مدیر دمو زنجیره ارزش',
    '$2b$12$dTFM.AIRyaHlm8xioKQLnegLWMo1PT8AwDuuZHNO6SWHTD5QFUyyS',
    '3MYXLVCKBIRJUTD6',
    'admin',
    'fa'
)
ON CONFLICT (employee_code) DO NOTHING;

-- ---------------------------------------------------------------------
-- فاز ۵: Audit Log امنیتی/عملیاتی (NFR-SEC)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    action          VARCHAR(128) NOT NULL,
    actor           VARCHAR(128) NOT NULL,
    resource        VARCHAR(256),
    outcome         VARCHAR(32) NOT NULL DEFAULT 'success',
    ip              VARCHAR(64),
    details_json    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action);
