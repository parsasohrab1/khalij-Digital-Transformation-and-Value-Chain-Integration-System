"""Loading the inventory and price time series into TimescaleDB."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import psycopg2
import psycopg2.extras

from shared.settings import get_settings

from .connectors.base import RawRecord

logger = logging.getLogger(__name__)
settings = get_settings()

_MEMORY_TS: dict[str, list[dict[str, Any]]] = {"inventory": [], "prices": []}


def _ts_dsn() -> str:
    return settings.timescale_dsn.replace("postgresql+psycopg2", "postgresql")


def load_inventory_and_prices(records: list[RawRecord]) -> int:
    inv_rows = []
    price_rows = []
    for r in records:
        ts = r.timestamp or datetime.utcnow()
        if r.warehouse_code:
            inv_rows.append(
                (
                    ts,
                    r.warehouse_code,
                    (r.grade or "HDPE").upper(),
                    float(r.quantity if (r.uom or "").lower() in {"ton", "t", "mt"} else r.quantity * 0.001),
                    None,
                )
            )
        if r.oil_price is not None:
            price_rows.append(
                (
                    ts,
                    r.oil_price,
                    r.price_hdpe,
                    r.price_pp,
                    r.feedstock_price,
                    None,
                )
            )

    written = 0
    try:
        with psycopg2.connect(_ts_dsn()) as conn, conn.cursor() as cur:
            if inv_rows:
                psycopg2.extras.execute_batch(
                    cur,
                    """
                    INSERT INTO inventory_ts (time, warehouse_code, product_grade, quantity_tons, fill_rate_pct)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    inv_rows,
                    page_size=200,
                )
                written += len(inv_rows)
            if price_rows:
                psycopg2.extras.execute_batch(
                    cur,
                    """
                    INSERT INTO market_prices_ts
                        (time, oil_price_usd_bbl, price_hdpe_usd_ton, price_pp_usd_ton, feedstock_price_usd_ton, fx_usd_irr)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    """,
                    price_rows,
                    page_size=200,
                )
                written += len(price_rows)
            conn.commit()
        return written
    except Exception as exc:  # noqa: BLE001
        logger.warning("Timescale write failed, buffering memory: %s", exc)
        for row in inv_rows:
            _MEMORY_TS["inventory"].append(
                {
                    "time": row[0].isoformat() if hasattr(row[0], "isoformat") else row[0],
                    "warehouse_code": row[1],
                    "product_grade": row[2],
                    "quantity_tons": row[3],
                }
            )
        for row in price_rows:
            _MEMORY_TS["prices"].append(
                {
                    "time": row[0].isoformat() if hasattr(row[0], "isoformat") else row[0],
                    "oil_price_usd_bbl": row[1],
                    "price_hdpe_usd_ton": row[2],
                    "price_pp_usd_ton": row[3],
                    "feedstock_price_usd_ton": row[4],
                }
            )
        return len(inv_rows) + len(price_rows)


def memory_stats() -> dict[str, int]:
    return {k: len(v) for k, v in _MEMORY_TS.items()}
