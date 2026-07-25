"""تولید KPI و سری‌زمانی با فیلتر شرکت/محصول/منطقه/بازه."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from .catalog import PERIODS, SUBSIDIARIES


def _seed_from_filters(
    subsidiary_code: str | None,
    product_grade: str | None,
    region: str | None,
    period: str,
) -> int:
    raw = f"{subsidiary_code}|{product_grade}|{region}|{period}"
    return abs(hash(raw)) % (2**32)


def _filter_factor(
    subsidiary_code: str | None,
    product_grade: str | None,
    region: str | None,
) -> float:
    f = 1.0
    if subsidiary_code:
        f *= 0.92 + 0.04 * (sum(ord(c) for c in subsidiary_code) % 5)
    if product_grade == "HDPE":
        f *= 1.05
    elif product_grade == "PET":
        f *= 0.95
    if region == "Assaluyeh":
        f *= 1.03
    elif region == "Tehran":
        f *= 0.98
    return f


def build_kpis(
    *,
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, Any]:
    days = PERIODS.get(period, 30)
    rng = np.random.default_rng(_seed_from_filters(subsidiary_code, product_grade, region, period))
    factor = _filter_factor(subsidiary_code, product_grade, region)

    kpis = {
        "otif_percent": round(float(np.clip(88 + rng.normal(0, 2), 70, 99) * min(factor, 1.05)), 2),
        "warehouse_fill_rate_percent": round(float(np.clip(72 + rng.normal(0, 3), 40, 95)), 2),
        "operating_margin_percent": round(float(np.clip(21 + rng.normal(0, 1.5), 10, 35) * factor), 2),
        "orders_today": int(max(10, rng.integers(40, 120) * factor)),
        "ships_in_port": int(rng.integers(1, 5)),
        "avg_eta_days": round(float(np.clip(6.5 + rng.normal(0, 0.8), 2, 15)), 1),
        "sales_usd_period": round(float(rng.uniform(1.2e6, 3.5e6) * factor * (days / 30)), 2),
        "cost_per_ton_usd": round(float(980 + rng.normal(0, 25)), 2),
        "distribution_otif_gap": round(float(rng.normal(0, 3)), 2),
    }
    return kpis


def build_timeseries(
    *,
    metric: str = "operating_margin_percent",
    period: str = "30d",
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    days = PERIODS.get(period, 30)
    rng = np.random.default_rng(_seed_from_filters(subsidiary_code, product_grade, region, period) + 11)
    factor = _filter_factor(subsidiary_code, product_grade, region)
    base_map = {
        "operating_margin_percent": 21.0,
        "otif_percent": 88.0,
        "warehouse_fill_rate_percent": 72.0,
        "orders": 70.0,
        "sales_usd": 8.0e4,
    }
    base = base_map.get(metric, 50.0) * factor
    start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    points = []
    for i in range(days):
        d = start + timedelta(days=i)
        seasonal = 1.0 + 0.04 * np.sin(2 * np.pi * i / max(days, 1))
        noise = 1.0 + float(rng.normal(0, 0.03))
        value = base * seasonal * noise
        if metric.endswith("percent"):
            value = float(np.clip(value, 5, 99))
        points.append({"date": d.isoformat(), "value": round(float(value), 2)})
    return {"metric": metric, "period": period, "points": points}


def distribution_performance(
    *,
    subsidiary_code: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, Any]:
    rng = np.random.default_rng(_seed_from_filters(subsidiary_code, None, region, period) + 3)
    rows = []
    for sub in SUBSIDIARIES:
        if subsidiary_code and sub["code"] != subsidiary_code:
            continue
        if region and sub["region"] != region:
            continue
        rows.append(
            {
                "subsidiary_code": sub["code"],
                "region": sub["region"],
                "otif_percent": round(float(np.clip(85 + rng.normal(0, 4), 70, 99)), 2),
                "avg_eta_days": round(float(np.clip(6 + rng.normal(0, 1.2), 2, 14)), 1),
                "logistics_cost_per_ton_usd": round(float(45 + rng.normal(0, 6)), 2),
                "on_time_shipments": int(rng.integers(20, 90)),
                "delayed_shipments": int(rng.integers(0, 12)),
            }
        )
    return {"period": period, "rows": rows}
