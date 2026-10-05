"""Loading and filtering value chain CSV data for BI."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from shared.settings import get_settings

from .catalog import PERIODS, PRODUCTS, REGIONS, SUBSIDIARIES

_SUB_CODES = [s["code"] for s in SUBSIDIARIES]
_REGION_BY_SUB = {s["code"]: s["region"] for s in SUBSIDIARIES}


def _candidate_paths() -> list[Path]:
    settings = get_settings()
    root = Path(__file__).resolve().parents[3]
    return [
        Path(settings.synthetic_data_path),
        root / "data" / "digital_value_chain_data_10k.csv",
        Path("/app/data/digital_value_chain_data_10k.csv"),
        Path("data/digital_value_chain_data_10k.csv"),
    ]


@lru_cache(maxsize=1)
def load_frame() -> pd.DataFrame | None:
    for path in _candidate_paths():
        try:
            if path.exists() and path.stat().st_size > 1000:
                df = pd.read_csv(path, parse_dates=["timestamp"])
                return _enrich(df)
        except Exception:  # noqa: BLE001
            continue
    return None


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "product_type" not in out.columns and "product_grade" in out.columns:
        out["product_type"] = out["product_grade"]
    n = len(out)
    if "subsidiary_code" not in out.columns:
        out["subsidiary_code"] = [_SUB_CODES[i % len(_SUB_CODES)] for i in range(n)]
    if "region" not in out.columns:
        out["region"] = out["subsidiary_code"].map(_REGION_BY_SUB).fillna(REGIONS[0])
    return out


def filtered_frame(
    *,
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> pd.DataFrame | None:
    df = load_frame()
    if df is None or df.empty:
        return None
    out = df
    if product_grade:
        out = out[out["product_type"] == product_grade]
    if subsidiary_code:
        out = out[out["subsidiary_code"] == subsidiary_code]
    if region:
        out = out[out["region"] == region]
    if out.empty:
        out = df
    days = PERIODS.get(period, 30)
    # High-frequency synthetic series (~10k seconds): take proportional tail
    take = max(200, int(len(out) * (days / 90.0)))
    return out.tail(take).copy()


def data_source_meta() -> dict[str, Any]:
    df = load_frame()
    return {
        "source": "csv" if df is not None else "synthetic_fallback",
        "rows": 0 if df is None else int(len(df)),
        "products": PRODUCTS,
    }
