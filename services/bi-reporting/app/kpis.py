"""Generate KPIs and time series from real CSV (with deterministic fallback)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np

from .catalog import PERIODS, SUBSIDIARIES, UNIT_COST_BASE, UNIT_META
from .data_source import filtered_frame


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


def _fallback_kpis(
    *,
    subsidiary_code: str | None,
    product_grade: str | None,
    region: str | None,
    period: str,
) -> dict[str, Any]:
    days = PERIODS.get(period, 30)
    rng = np.random.default_rng(_seed_from_filters(subsidiary_code, product_grade, region, period))
    factor = _filter_factor(subsidiary_code, product_grade, region)
    return {
        "otif_percent": round(float(np.clip(88 + rng.normal(0, 2), 70, 99) * min(factor, 1.05)), 2),
        "warehouse_fill_rate_percent": round(float(np.clip(72 + rng.normal(0, 3), 40, 95)), 2),
        "operating_margin_percent": round(float(np.clip(21 + rng.normal(0, 1.5), 10, 35) * factor), 2),
        "orders_today": int(max(10, rng.integers(40, 120) * factor)),
        "ships_in_port": int(rng.integers(1, 5)),
        "avg_eta_days": round(float(np.clip(6.5 + rng.normal(0, 0.8), 2, 15)), 1),
        "sales_usd_period": round(float(rng.uniform(1.2e6, 3.5e6) * factor * (days / 30)), 2),
        "cost_per_ton_usd": round(float(980 + rng.normal(0, 25)), 2),
        "distribution_otif_gap": round(float(rng.normal(0, 3)), 2),
        "data_source": "synthetic_fallback",
    }


def build_kpis(
    *,
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, Any]:
    df = filtered_frame(
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
        period=period,
    )
    if df is None or df.empty:
        return _fallback_kpis(
            subsidiary_code=subsidiary_code,
            product_grade=product_grade,
            region=region,
            period=period,
        )

    feedstock = float(df["feedstock_price_usd_ton"].mean()) if "feedstock_price_usd_ton" in df else 800.0
    logistics = float(df["logistics_cost_per_ton_usd"].mean()) if "logistics_cost_per_ton_usd" in df else 50.0
    price_col = "price_hdpe_usd_ton" if "price_hdpe_usd_ton" in df else None
    revenue = float(df[price_col].mean()) if price_col else feedstock * 1.3
    cost = feedstock + logistics + 120.0

    return {
        "otif_percent": round(float(df["otif_rate_percent"].mean()), 2),
        "warehouse_fill_rate_percent": round(float(df["warehouse_fill_rate_percent"].mean()), 2),
        "operating_margin_percent": round(float(df["operating_margin_percent"].mean()), 2),
        "orders_today": int(df["orders_received"].tail(min(86_400, len(df))).sum()),
        "ships_in_port": int(round(float(df["ships_in_port"].tail(100).mean()))),
        "avg_eta_days": round(float(df["eta_days"].mean()), 1),
        "sales_usd_period": round(float(df["order_value_usd"].sum()), 2),
        "cost_per_ton_usd": round(cost, 2),
        "distribution_otif_gap": round(float(90.0 - df["otif_rate_percent"].mean()), 2),
        "data_source": "csv",
        "sample_rows": int(len(df)),
        "implied_margin_per_ton_usd": round(revenue - cost, 2),
    }


def build_timeseries(
    *,
    metric: str = "operating_margin_percent",
    period: str = "30d",
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    days = PERIODS.get(period, 30)
    df = filtered_frame(
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
        period=period,
    )
    col_map = {
        "operating_margin_percent": "operating_margin_percent",
        "otif_percent": "otif_rate_percent",
        "warehouse_fill_rate_percent": "warehouse_fill_rate_percent",
        "orders": "orders_received",
        "sales_usd": "order_value_usd",
    }
    col = col_map.get(metric, "operating_margin_percent")

    if df is not None and not df.empty and col in df.columns:
        # Bucket into `days` points
        chunk = max(1, len(df) // days)
        points = []
        start = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
        for i in range(days):
            sl = df.iloc[i * chunk : (i + 1) * chunk]
            if sl.empty:
                sl = df.tail(chunk)
            value = float(sl[col].mean())
            points.append({"date": (start + timedelta(days=i)).isoformat(), "value": round(value, 2)})
        return {"metric": metric, "period": period, "points": points, "data_source": "csv"}

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
    return {"metric": metric, "period": period, "points": points, "data_source": "synthetic_fallback"}


def distribution_performance(
    *,
    subsidiary_code: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, Any]:
    df = filtered_frame(subsidiary_code=subsidiary_code, region=region, period=period)
    rows = []
    for sub in SUBSIDIARIES:
        if subsidiary_code and sub["code"] != subsidiary_code:
            continue
        if region and sub["region"] != region:
            continue
        if df is not None and not df.empty:
            part = df[df["subsidiary_code"] == sub["code"]]
            if part.empty:
                part = df
            delayed = int(max(0, round((95 - float(part["otif_rate_percent"].mean())) / 2)))
            rows.append(
                {
                    "subsidiary_code": sub["code"],
                    "region": sub["region"],
                    "otif_percent": round(float(part["otif_rate_percent"].mean()), 2),
                    "avg_eta_days": round(float(part["eta_days"].mean()), 1),
                    "logistics_cost_per_ton_usd": round(float(part["logistics_cost_per_ton_usd"].mean()), 2),
                    "on_time_shipments": int(max(1, round(float(part["otif_rate_percent"].mean())))),
                    "delayed_shipments": delayed,
                }
            )
        else:
            rng = np.random.default_rng(_seed_from_filters(sub["code"], None, sub["region"], period) + 3)
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
    return {"period": period, "rows": rows, "data_source": "csv" if df is not None else "synthetic_fallback"}


def csv_adjusted_unit_costs(
    *,
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, dict[str, float]]:
    """Adjust static unit costs with live CSV feedstock/logistics averages."""
    df = filtered_frame(
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
        period=period,
    )
    out: dict[str, dict[str, float]] = {k: dict(v) for k, v in UNIT_COST_BASE.items()}
    if df is None or df.empty:
        return out
    feed = float(df["feedstock_price_usd_ton"].mean())
    logi = float(df["logistics_cost_per_ton_usd"].mean())
    hdpe = float(df["price_hdpe_usd_ton"].mean()) if "price_hdpe_usd_ton" in df else None
    pp = float(df["price_pp_usd_ton"].mean()) if "price_pp_usd_ton" in df else None
    for code, costs in out.items():
        meta = UNIT_META[code]
        costs["feedstock"] = round(0.55 * costs["feedstock"] + 0.45 * feed, 2)
        costs["logistics"] = round(0.5 * costs["logistics"] + 0.5 * logi, 2)
        if meta["product"] in {"HDPE", "LDPE", "LLDPE"} and hdpe:
            costs["revenue"] = round(0.4 * costs["revenue"] + 0.6 * hdpe, 2)
        elif meta["product"] == "PP" and pp:
            costs["revenue"] = round(0.4 * costs["revenue"] + 0.6 * pp, 2)
    return out
