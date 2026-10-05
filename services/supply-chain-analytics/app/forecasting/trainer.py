"""Training and serving demand forecasts per grade on historical CSV."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from shared.settings import get_settings

from .lstm_model import forecast_lstm
from .prophet_like import forecast_prophet

logger = logging.getLogger(__name__)
settings = get_settings()

GRADES = ["HDPE", "LDPE", "LLDPE", "PP", "PET"]
_MODEL_CACHE: dict[str, Any] = {}


def _resolve_csv(path: str | None = None) -> Path | None:
    candidates = [
        Path(path) if path else None,
        Path(settings.synthetic_data_path),
        Path("data/digital_value_chain_data_10k.csv"),
        Path("/app/data/digital_value_chain_data_10k.csv"),
    ]
    return next((p for p in candidates if p and p.exists()), None)


def load_grade_series(csv_path: str | None = None) -> dict[str, np.ndarray]:
    path = _resolve_csv(csv_path)
    if path is None:
        rng = np.random.default_rng(42)
        return {g: rng.poisson(2, 500).astype(float) * (20 + i * 5) for i, g in enumerate(GRADES)}

    df = pd.read_csv(path)
    series: dict[str, np.ndarray] = {}
    for g in GRADES:
        part = df[df["product_type"] == g]["order_quantity_tons"].to_numpy(dtype=float)
        if len(part) < 50:
            part = df["order_quantity_tons"].to_numpy(dtype=float)
        series[g] = part
    return series


def train_and_forecast(
    horizon_days: int = 90,
    model_name: str | None = None,
    oil_price: float = 75.0,
    csv_path: str | None = None,
) -> dict[str, Any]:
    """Forecast over a horizon_days horizon — approximates per-second data into daily buckets."""
    model_name = (model_name or settings.forecast_model).lower()
    series = load_grade_series(csv_path)

    # Approximation: every ~86400 seconds ≈ 1 day; in the 10k-second data ~ 2.7 hours → 60-sample buckets are treated as "artificial days"
    bucket = 60
    demand_tons: dict[str, float] = {}
    details: dict[str, Any] = {}
    oil_factor = 1.0 + 0.004 * (oil_price - 75)

    for g, y in series.items():
        # aggregate to pseudo-daily (bucket mean, not sum — for realistic scale)
        n = len(y) - (len(y) % bucket)
        if n < bucket * 3:
            daily = y
        else:
            daily = y[:n].reshape(-1, bucket).mean(axis=1)

        steps = max(min(horizon_days, 90), 7)
        if model_name == "lstm":
            result = forecast_lstm(daily, horizon=steps, window=min(16, max(4, len(daily) // 4)))
        elif model_name == "ensemble":
            p = forecast_prophet(daily, horizon=steps, period=max(7.0, len(daily) / 4))
            l = forecast_lstm(daily, horizon=steps, window=min(16, max(4, len(daily) // 4)))
            preds = 0.6 * np.array(p["predictions"]) + 0.4 * np.array(l["predictions"])
            result = {
                "model": "ensemble",
                "predictions": preds.tolist(),
                "total": float(np.sum(preds)),
                "train_mean": p["train_mean"],
                "params": {"prophet": p["params"], "lstm": l["params"]},
            }
        else:
            result = forecast_prophet(daily, horizon=steps, period=max(7.0, len(daily) / 4))

        preds = np.array(result["predictions"], dtype=float)
        # Horizon extension: daily mean forecast × number of days
        daily_avg = float(np.mean(preds)) if len(preds) else float(result.get("train_mean", 0))
        demand_tons[g] = round(daily_avg * horizon_days * oil_factor, 2)
        details[g] = result

    _MODEL_CACHE["last"] = {"model": model_name, "demand_tons": demand_tons, "details": details}
    return {
        "horizon_days": horizon_days,
        "model": model_name,
        "demand_tons": demand_tons,
        "oil_price_usd_bbl": oil_price,
        "grade_details": {g: {"total": details[g]["total"], "model": details[g]["model"]} for g in GRADES},
    }


def last_trained() -> dict[str, Any]:
    return _MODEL_CACHE.get("last") or {}
