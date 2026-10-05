"""Monitoring drift of actual demand against the training baseline."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np

from shared.schemas import DriftReport
from shared.settings import get_settings

from ..forecasting.trainer import load_grade_series

settings = get_settings()


def compute_drift(grade: str = "HDPE", recent_window: int = 200) -> DriftReport:
    series = load_grade_series()
    y = series.get(grade)
    if y is None:
        y = next(iter(series.values()))
    if len(y) < recent_window * 2:
        recent_window = max(10, len(y) // 3)
    baseline = y[: len(y) - recent_window]
    current = y[-recent_window:]
    b_mean = float(np.mean(baseline))
    c_mean = float(np.mean(current))
    score = abs(c_mean - b_mean) / (abs(b_mean) + 1e-9)
    return DriftReport(
        metric=f"demand_{grade}",
        baseline_mean=round(b_mean, 4),
        current_mean=round(c_mean, 4),
        drift_score=round(score, 4),
        threshold=settings.drift_threshold,
        is_drifted=score > settings.drift_threshold,
        checked_at=datetime.now(timezone.utc),
    )


def compute_all_grades_drift() -> list[DriftReport]:
    from ..forecasting.trainer import GRADES

    return [compute_drift(g) for g in GRADES]
