"""پیکربندی مشترک تمام سرویس‌ها؛ مقادیر از متغیرهای محیطی (.env) خوانده می‌شوند."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_locale: str = Field(default="fa", alias="DEFAULT_LOCALE")

    postgres_dsn: str = Field(
        default="postgresql+psycopg2://khalij_admin:change_me@postgres:5432/khalij_dvc",
        alias="POSTGRES_DSN",
    )
    timescale_dsn: str = Field(
        default="postgresql+psycopg2://khalij_admin:change_me@timescaledb:5432/khalij_dvc_ts",
        alias="TIMESCALE_DSN",
    )

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

    kafka_bootstrap_servers: str = Field(default="kafka:9092", alias="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic_orders: str = Field(default="dvc.orders", alias="KAFKA_TOPIC_ORDERS")
    kafka_topic_inventory: str = Field(default="dvc.inventory", alias="KAFKA_TOPIC_INVENTORY")
    kafka_topic_logistics: str = Field(default="dvc.logistics", alias="KAFKA_TOPIC_LOGISTICS")
    kafka_topic_prices: str = Field(default="dvc.prices", alias="KAFKA_TOPIC_PRICES")
    kafka_topic_alerts: str = Field(default="dvc.alerts", alias="KAFKA_TOPIC_ALERTS")
    kafka_topic_subsidiary_prefix: str = Field(
        default="dvc.subsidiary", alias="KAFKA_TOPIC_SUBSIDIARY_PREFIX"
    )
    kafka_consumer_group: str = Field(default="khalij-dvc", alias="KAFKA_CONSUMER_GROUP")

    mlflow_tracking_uri: str = Field(default="http://mlflow:5000", alias="MLFLOW_TRACKING_URI")

    demand_forecast_horizon_days: int = Field(default=90, alias="DEMAND_FORECAST_HORIZON_DAYS")
    lp_solver_time_limit_sec: int = Field(default=30, alias="LP_SOLVER_TIME_LIMIT_SEC")
    holding_margin_objective: str = Field(default="maximize", alias="HOLDING_MARGIN_OBJECTIVE")
    forecast_model: str = Field(default="prophet", alias="FORECAST_MODEL")  # prophet | lstm | ensemble
    forecast_cache_ttl_sec: int = Field(default=120, alias="FORECAST_CACHE_TTL_SEC")
    drift_threshold: float = Field(default=0.25, alias="DRIFT_THRESHOLD")
    synthetic_data_path: str = Field(
        default="data/digital_value_chain_data_10k.csv", alias="SYNTHETIC_DATA_PATH"
    )

    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    two_factor_required: bool = Field(default=True, alias="TWO_FACTOR_REQUIRED")

    # Phase 5 — Security / Scale (NFR-SEC / NFR-SCL / NFR-AVAIL)
    encryption_key: str = Field(
        default="0123456789abcdef0123456789abcdef",  # 32-byte hex fallback for AES-256
        alias="ENCRYPTION_KEY",
    )
    tls_min_version: str = Field(default="TLSv1.3", alias="TLS_MIN_VERSION")
    force_https: bool = Field(default=False, alias="FORCE_HTTPS")
    rate_limit_per_minute: int = Field(default=120, alias="RATE_LIMIT_PER_MINUTE")
    audit_log_enabled: bool = Field(default=True, alias="AUDIT_LOG_ENABLED")
    target_availability: str = Field(default="99.95%", alias="TARGET_AVAILABILITY")
    target_tps: int = Field(default=50000, alias="TARGET_TPS")

    api_gateway_port: int = Field(default=8000, alias="API_GATEWAY_PORT")
    data_integration_port: int = Field(default=8001, alias="DATA_INTEGRATION_PORT")
    supply_chain_analytics_port: int = Field(default=8002, alias="SUPPLY_CHAIN_ANALYTICS_PORT")
    logistics_port: int = Field(default=8003, alias="LOGISTICS_PORT")
    order_to_cash_port: int = Field(default=8004, alias="ORDER_TO_CASH_PORT")
    bi_reporting_port: int = Field(default=8005, alias="BI_REPORTING_PORT")
    command_center_port: int = Field(default=8010, alias="COMMAND_CENTER_PORT")
    customer_portal_port: int = Field(default=8011, alias="CUSTOMER_PORTAL_PORT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
