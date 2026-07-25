"""اسکیماهای مشترک Pydantic برای رویدادها و APIهای زنجیره ارزش."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ProductGrade = Literal["HDPE", "LDPE", "LLDPE", "PP", "PET"]
OrderChannel = Literal["online", "contract", "auction"]
ShipmentMode = Literal["sea", "road", "rail"]
IranPort = Literal["BandarAbbas", "Assaluyeh", "Bushehr", "ImamKhomeini", "Chabahar"]


class DomainOwnership(BaseModel):
    """مالکیت دامنه داده در معماری Data Mesh (نوآوری ثبت اختراع)."""

    subsidiary_code: str
    domain_owner: str
    kafka_topic: str
    source_system: str = Field(description="Oracle | SQLServer | PostgreSQL | SAP | ERP")


class OrderEvent(BaseModel):
    order_number: str
    channel: OrderChannel
    product_grade: ProductGrade
    quantity_tons: float
    value_usd: float
    subsidiary_code: str
    timestamp: datetime
    hs_code: str | None = None
    internal_code: str | None = None


class InventorySnapshot(BaseModel):
    warehouse_code: str
    product_grade: ProductGrade
    quantity_tons: float
    fill_rate_pct: float
    timestamp: datetime
    subsidiary_code: str | None = None


class PriceTick(BaseModel):
    timestamp: datetime
    oil_price_usd_bbl: float
    price_hdpe_usd_ton: float
    price_pp_usd_ton: float
    feedstock_price_usd_ton: float
    fx_usd_irr: float | None = None


class ShipmentPosition(BaseModel):
    shipment_number: str
    latitude: float
    longitude: float
    speed_knots: float | None = None
    source: Literal["GPS", "AIS"] = "GPS"
    timestamp: datetime


class FeedstockAllocation(BaseModel):
    unit_code: str
    feedstock_tons: float
    expected_margin_usd: float


class IntegratedOptimizationResult(BaseModel):
    """نتیجه بهینه‌سازی یکپارچه تقاضا + قیمت + تخصیص خوراک (FR-ML-01)."""

    holding_margin_usd: float
    demand_forecast: dict[str, float]
    price_forecast: dict[str, float]
    feedstock_allocations: list[FeedstockAllocation]
    horizon_days: int
    run_id: str | None = None
    model_name: str | None = None
    mlflow_run_id: str | None = None
    trading_decision: dict[str, Any] | None = None
    closed_loop: bool = True
    cache_hit: bool = False
    latency_ms: float | None = None


class DriftReport(BaseModel):
    metric: str
    baseline_mean: float
    current_mean: float
    drift_score: float
    threshold: float
    is_drifted: bool
    checked_at: datetime
