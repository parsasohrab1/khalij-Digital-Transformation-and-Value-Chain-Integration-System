"""Prophet-like model: linear trend + Fourier seasonality on historical demand."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ProphetLikeModel:
    trend_a: float
    trend_b: float
    fourier_cos: np.ndarray
    fourier_sin: np.ndarray
    period: float
    n_harmonics: int
    train_mean: float
    train_std: float

    def predict_from(self, t0: float, steps: int) -> np.ndarray:
        t = np.arange(t0, t0 + steps, dtype=float)
        y = self.trend_a + self.trend_b * t
        for k in range(self.n_harmonics):
            angle = 2 * np.pi * (k + 1) * t / self.period
            y += self.fourier_cos[k] * np.cos(angle) + self.fourier_sin[k] * np.sin(angle)
        return np.maximum(y, 0.0)


def fit_prophet_like(y: np.ndarray, period: float = 24 * 3600, n_harmonics: int = 3) -> ProphetLikeModel:
    """y: demand series (e.g., orders_received or order_quantity)."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    t = np.arange(n, dtype=float)

    # Design matrix: [1, t, cos1, sin1, ...]
    cols = [np.ones(n), t]
    for k in range(n_harmonics):
        angle = 2 * np.pi * (k + 1) * t / period
        cols.append(np.cos(angle))
        cols.append(np.sin(angle))
    X = np.column_stack(cols)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)

    return ProphetLikeModel(
        trend_a=float(coef[0]),
        trend_b=float(coef[1]),
        fourier_cos=np.array([coef[2 + 2 * k] for k in range(n_harmonics)]),
        fourier_sin=np.array([coef[3 + 2 * k] for k in range(n_harmonics)]),
        period=period,
        n_harmonics=n_harmonics,
        train_mean=float(np.mean(y)),
        train_std=float(np.std(y) + 1e-9),
    )


def forecast_prophet(y: np.ndarray, horizon: int, period: float = 86400.0) -> dict:
    model = fit_prophet_like(y, period=period)
    preds = model.predict_from(float(len(y)), horizon)
    return {
        "model": "prophet-like",
        "predictions": preds.tolist(),
        "total": float(np.sum(preds)),
        "train_mean": model.train_mean,
        "params": {"trend_a": model.trend_a, "trend_b": model.trend_b, "n_harmonics": model.n_harmonics},
    }
