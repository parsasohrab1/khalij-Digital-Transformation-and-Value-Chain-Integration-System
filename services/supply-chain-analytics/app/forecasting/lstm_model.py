"""Light LSTM with NumPy for demand sequence forecasting (without PyTorch dependency)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -20, 20)))


def _tanh(x: np.ndarray) -> np.ndarray:
    return np.tanh(np.clip(x, -20, 20))


@dataclass
class TinyLSTM:
    W_f: np.ndarray
    U_f: np.ndarray
    b_f: np.ndarray
    W_i: np.ndarray
    U_i: np.ndarray
    b_i: np.ndarray
    W_c: np.ndarray
    U_c: np.ndarray
    b_c: np.ndarray
    W_o: np.ndarray
    U_o: np.ndarray
    b_o: np.ndarray
    W_y: np.ndarray
    b_y: np.ndarray
    window: int
    y_mean: float
    y_std: float

    def step(self, x: float, h: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        xv = np.array([x], dtype=float)
        f = _sigmoid(self.W_f @ xv + self.U_f @ h + self.b_f)
        i = _sigmoid(self.W_i @ xv + self.U_i @ h + self.b_i)
        g = _tanh(self.W_c @ xv + self.U_c @ h + self.b_c)
        o = _sigmoid(self.W_o @ xv + self.U_o @ h + self.b_o)
        c_new = f * c + i * g
        h_new = o * _tanh(c_new)
        y = float(self.W_y @ h_new + self.b_y)
        return h_new, c_new, y

    def predict_horizon(self, seed: np.ndarray, steps: int) -> np.ndarray:
        h = np.zeros(self.W_y.shape[0])
        c = np.zeros(self.W_y.shape[0])
        # warm-up
        for x in seed[-self.window :]:
            h, c, _ = self.step(float(x), h, c)
        preds = []
        last = float(seed[-1])
        for _ in range(steps):
            h, c, y = self.step(last, h, c)
            # denormalize prediction was trained on normalized; keep relative
            preds.append(max(y, 0.0))
            last = y
        return np.array(preds, dtype=float)


def _init_lstm(hidden: int = 8, rng: np.random.Generator | None = None) -> dict:
    rng = rng or np.random.default_rng(42)
    scale = 0.1
    return {
        "W_f": rng.normal(0, scale, (hidden, 1)),
        "U_f": rng.normal(0, scale, (hidden, hidden)),
        "b_f": np.ones(hidden),
        "W_i": rng.normal(0, scale, (hidden, 1)),
        "U_i": rng.normal(0, scale, (hidden, hidden)),
        "b_i": np.zeros(hidden),
        "W_c": rng.normal(0, scale, (hidden, 1)),
        "U_c": rng.normal(0, scale, (hidden, hidden)),
        "b_c": np.zeros(hidden),
        "W_o": rng.normal(0, scale, (hidden, 1)),
        "U_o": rng.normal(0, scale, (hidden, hidden)),
        "b_o": np.zeros(hidden),
        "W_y": rng.normal(0, scale, (hidden,)),
        "b_y": np.array(0.0),
    }


def fit_lstm(y: np.ndarray, window: int = 32, epochs: int = 5, hidden: int = 8, lr: float = 0.01) -> TinyLSTM:
    """Very light training with an approximate gradient on the output (for the patent PoC)."""
    y = np.asarray(y, dtype=float)
    y_mean, y_std = float(np.mean(y)), float(np.std(y) + 1e-9)
    yn = (y - y_mean) / y_std
    params = _init_lstm(hidden)
    # Simple training: only W_y / b_y targeting the mean of the next window (more stable than full BPTT)
    for _ in range(epochs):
        for i in range(window, len(yn) - 1):
            target = yn[i]
            context = float(np.mean(yn[i - window : i]))
            pred = float(params["W_y"] @ (np.tanh(np.full(hidden, context))) + params["b_y"])
            err = pred - target
            params["W_y"] -= lr * err * np.tanh(np.full(hidden, context))
            params["b_y"] -= lr * err

    model = TinyLSTM(
        **params,
        window=window,
        y_mean=y_mean,
        y_std=y_std,
    )
    return model


def forecast_lstm(y: np.ndarray, horizon: int, window: int = 32) -> dict:
    model = fit_lstm(y, window=window)
    yn = (y - model.y_mean) / model.y_std
    preds_n = model.predict_horizon(yn, horizon)
    preds = preds_n * model.y_std + model.y_mean
    preds = np.maximum(preds, 0.0)
    return {
        "model": "lstm-numpy",
        "predictions": preds.tolist(),
        "total": float(np.sum(preds)),
        "train_mean": model.y_mean,
        "params": {"window": window, "hidden": int(model.W_y.shape[0])},
    }
