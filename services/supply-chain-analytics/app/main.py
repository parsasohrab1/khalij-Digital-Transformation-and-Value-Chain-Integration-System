"""Supply Chain Analytics — فاز ۲: Prophet/LSTM + بهینه‌سازی حلقه‌بسته + Trading what-if + MLflow/Drift.

نوآوری ثبت اختراع: پیش‌بینی و بهینه‌سازی یکپارچه با بیشینه‌سازی حاشیه کل هلدینگ.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis
from fastapi import FastAPI
from pydantic import BaseModel, Field

from shared.logging_config import configure_logging
from shared.schemas import DriftReport, IntegratedOptimizationResult
from shared.settings import get_settings

from .forecasting.trainer import last_trained, train_and_forecast
from .mlops.drift import compute_all_grades_drift, compute_drift
from .mlops.registry import list_runs, log_model_run
from .optimizer.integrated import DEFAULT_UNITS, run_integrated_optimization, solve_feedstock_lp
from .optimizer.trading_whatif import run_trading_whatif

settings = get_settings()
configure_logging("supply-chain-analytics", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - Supply Chain Analytics (Phase 2)",
    description="Prophet/LSTM + closed-loop LP + trading what-if + MLflow + drift",
    version="2.0.0",
)

_redis: redis.Redis | None = None
_MEMORY_CACHE: dict[str, str] = {}


def get_redis() -> redis.Redis | None:
    global _redis
    try:
        if _redis is None:
            _redis = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.5)
            _redis.ping()
        return _redis
    except Exception:  # noqa: BLE001
        _redis = None
        return None


def _cache_get(key: str) -> dict | None:
    r = get_redis()
    raw = None
    if r is not None:
        try:
            raw = r.get(key)
        except Exception:  # noqa: BLE001
            raw = None
    if raw is None:
        raw = _MEMORY_CACHE.get(key)
    return json.loads(raw) if raw else None


def _cache_set(key: str, value: dict, ttl: int | None = None) -> None:
    payload = json.dumps(value, default=str)
    ttl = ttl or settings.forecast_cache_ttl_sec
    r = get_redis()
    if r is not None:
        try:
            r.setex(key, ttl, payload)
            return
        except Exception:  # noqa: BLE001
            pass
    _MEMORY_CACHE[key] = payload


class DemandForecastRequest(BaseModel):
    horizon_days: int = Field(default=90, ge=7, le=180)
    oil_price_usd_bbl: float = 75.0
    fx_index: float = 1.0
    model: str | None = None  # prophet | lstm | ensemble


class FeedstockLPRequest(BaseModel):
    available_feedstock_tons: float = Field(default=3500, gt=0)
    units: list[dict] | None = None
    demand: dict[str, float] | None = None


class TradingOptimizeRequest(BaseModel):
    current_price: float = 900.0
    oil_price_usd_bbl: float = 75.0
    inventory_tons: float = 5000.0
    scenarios: list[dict[str, Any]] | None = None


class IntegratedOptimizeRequest(BaseModel):
    horizon_days: int = Field(default=90, ge=7, le=180)
    available_feedstock_tons: float = 3500.0
    oil_price_usd_bbl: float = 75.0
    model: str | None = None
    inventory_tons: float = 5000.0
    what_if: dict[str, Any] | None = None
    use_cache: bool = True


class TrainRequest(BaseModel):
    model: str = "ensemble"
    horizon_days: int = 90
    csv_path: str | None = None


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "supply-chain-analytics",
        "phase": 2,
        "patent": "integrated-demand-price-feedstock-optimization",
    }


@app.post("/forecast/demand")
async def forecast_demand(body: DemandForecastRequest) -> dict:
    cache_key = f"dvc:forecast:{body.model}:{body.horizon_days}:{body.oil_price_usd_bbl}"
    cached = _cache_get(cache_key)
    if cached:
        cached["cache_hit"] = True
        return cached

    result = train_and_forecast(
        horizon_days=body.horizon_days,
        model_name=body.model,
        oil_price=body.oil_price_usd_bbl * body.fx_index,
    )
    result["cache_hit"] = False
    _cache_set(cache_key, result)
    return result


@app.post("/optimize/feedstock")
async def optimize_feedstock(body: FeedstockLPRequest) -> dict:
    units = body.units or DEFAULT_UNITS
    allocations, total_margin = solve_feedstock_lp(body.available_feedstock_tons, units, body.demand)
    return {
        "available_feedstock_tons": body.available_feedstock_tons,
        "holding_margin_usd": total_margin,
        "allocations": [a.model_dump() for a in allocations],
        "solver": "CBC",
        "closed_loop_demand": body.demand is not None,
        "patent_claim": "holding-wide-margin-maximization-lp",
    }


@app.post("/optimize/trading")
async def optimize_trading(body: TradingOptimizeRequest) -> dict:
    return run_trading_whatif(
        current_price=body.current_price,
        oil_price=body.oil_price_usd_bbl,
        inventory_tons=body.inventory_tons,
        scenarios=body.scenarios,
    )


@app.post("/optimize/integrated", response_model=IntegratedOptimizationResult)
async def optimize_integrated(body: IntegratedOptimizeRequest) -> IntegratedOptimizationResult:
    raw = json.dumps(body.model_dump(), sort_keys=True, default=str)
    cache_key = "dvc:integrated:" + hashlib.sha256(raw.encode()).hexdigest()[:16]

    if body.use_cache:
        cached = _cache_get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return IntegratedOptimizationResult(**cached)

    result = run_integrated_optimization(
        horizon_days=body.horizon_days,
        available_feedstock_tons=body.available_feedstock_tons,
        oil_price_usd_bbl=body.oil_price_usd_bbl,
        model_name=body.model,
        inventory_tons=body.inventory_tons,
        what_if=body.what_if,
    )

    run_id = log_model_run(
        model_name=result.model_name or "integrated",
        metrics={
            "holding_margin_usd": result.holding_margin_usd,
            "latency_ms": result.latency_ms or 0.0,
            "horizon_days": float(result.horizon_days),
        },
        params={
            "oil_price": body.oil_price_usd_bbl,
            "feedstock": body.available_feedstock_tons,
            "model": body.model or settings.forecast_model,
        },
        tags={"patent": "closed-loop-value-chain", "phase": "2"},
    )
    result.mlflow_run_id = run_id

    payload = result.model_dump(mode="json")
    _cache_set(cache_key, payload)
    _cache_set("dvc:latest_integrated_optimization", payload, ttl=600)
    r = get_redis()
    if r is not None:
        try:
            r.setex("dvc:holding_margin_usd", 600, str(result.holding_margin_usd))
        except Exception:  # noqa: BLE001
            pass
    else:
        _MEMORY_CACHE["dvc:holding_margin_usd"] = str(result.holding_margin_usd)
    return result


@app.get("/optimize/latest")
async def latest_optimization() -> dict:
    cached = _cache_get("dvc:latest_integrated_optimization")
    return cached or {"status": "empty"}


@app.post("/train")
async def train_models(body: TrainRequest) -> dict:
    result = train_and_forecast(horizon_days=body.horizon_days, model_name=body.model, csv_path=body.csv_path)
    run_id = log_model_run(
        model_name=body.model,
        metrics={"demand_total": float(sum(result["demand_tons"].values()))},
        params={"horizon_days": body.horizon_days},
        tags={"task": "train"},
    )
    return {"status": "trained", "mlflow_run_id": run_id, "result": result, "cached_model": last_trained().get("model")}


@app.get("/mlflow/runs")
async def mlflow_runs(limit: int = 20) -> list[dict]:
    return list_runs(limit)


@app.get("/drift", response_model=list[DriftReport])
async def drift_all() -> list[DriftReport]:
    return compute_all_grades_drift()


@app.get("/drift/{grade}", response_model=DriftReport)
async def drift_one(grade: str) -> DriftReport:
    return compute_drift(grade.upper())
