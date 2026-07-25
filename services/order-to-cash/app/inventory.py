"""موجودی واقعی انبارها به‌تفکیک گرید محصول."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

WAREHOUSE_MASTER = [
    {
        "code": "WH-BND",
        "city": "Bandar Abbas",
        "lat": 27.1832,
        "lon": 56.2666,
        "port_code": "IRBND",
        "cost_per_ton": 45.0,
        "capacity_tons": 8000.0,
    },
    {
        "code": "WH-THR",
        "city": "Tehran",
        "lat": 35.6892,
        "lon": 51.3890,
        "port_code": None,
        "cost_per_ton": 55.0,
        "capacity_tons": 6000.0,
    },
    {
        "code": "WH-ASL",
        "city": "Assaluyeh",
        "lat": 27.4761,
        "lon": 52.6070,
        "port_code": "IRASL",
        "cost_per_ton": 40.0,
        "capacity_tons": 12000.0,
    },
]

GRADES = ["HDPE", "LDPE", "LLDPE", "PP", "PET"]

# inventory[warehouse][grade] = tons
_INVENTORY: dict[str, dict[str, float]] = {
    "WH-BND": {"HDPE": 2200, "LDPE": 900, "LLDPE": 800, "PP": 700, "PET": 400},
    "WH-THR": {"HDPE": 1100, "LDPE": 600, "LLDPE": 500, "PP": 500, "PET": 300},
    "WH-ASL": {"HDPE": 3500, "LDPE": 1400, "LLDPE": 1200, "PP": 1100, "PET": 800},
}


def list_inventory() -> list[dict[str, Any]]:
    rows = []
    for wh in WAREHOUSE_MASTER:
        inv = _INVENTORY[wh["code"]]
        total = sum(inv.values())
        rows.append(
            {
                **wh,
                "by_grade": deepcopy(inv),
                "total_tons": round(total, 2),
                "fill_rate_pct": round(100 * total / wh["capacity_tons"], 2),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    return rows


def available(warehouse_code: str, grade: str) -> float:
    return float(_INVENTORY.get(warehouse_code, {}).get(grade.upper(), 0.0))


def reserve(warehouse_code: str, grade: str, tons: float) -> float:
    g = grade.upper()
    cur = available(warehouse_code, g)
    if tons > cur + 1e-9:
        raise ValueError(f"insufficient inventory at {warehouse_code} for {g}: have={cur}, need={tons}")
    _INVENTORY[warehouse_code][g] = round(cur - tons, 3)
    return _INVENTORY[warehouse_code][g]


def restock(warehouse_code: str, grade: str, tons: float) -> float:
    g = grade.upper()
    _INVENTORY.setdefault(warehouse_code, {x: 0.0 for x in GRADES})
    _INVENTORY[warehouse_code][g] = round(available(warehouse_code, g) + tons, 3)
    return _INVENTORY[warehouse_code][g]


def snapshot_for_allocation(grade: str) -> list[dict[str, Any]]:
    g = grade.upper()
    out = []
    for wh in WAREHOUSE_MASTER:
        out.append({**wh, "inventory": available(wh["code"], g), "grade": g})
    return out
