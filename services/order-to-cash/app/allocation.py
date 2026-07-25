"""تخصیص هوشمند سفارش به انبار: موجودی واقعی + فاصله + هزینه حمل."""
from __future__ import annotations

import math
from typing import Any

from .inventory import snapshot_for_allocation


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def allocate(
    *,
    quantity_tons: float,
    product_grade: str,
    customer_lat: float,
    customer_lon: float,
    prefer_port: bool = True,
) -> dict[str, Any]:
    candidates = []
    for wh in snapshot_for_allocation(product_grade):
        if wh["inventory"] < quantity_tons:
            continue
        dist = haversine_km(customer_lat, customer_lon, wh["lat"], wh["lon"])
        # امتیاز: فاصله نرمال + هزینه + پاداش انبار بندری برای صادرات
        score = (dist / 1000.0) + (wh["cost_per_ton"] / 50.0)
        if prefer_port and wh.get("port_code"):
            score -= 0.15
        # موجودی بیشتر کمی بهتر است (پایداری)
        score -= min(wh["inventory"] / 20000.0, 0.1)
        candidates.append(
            {
                **wh,
                "distance_km": round(dist, 1),
                "score": round(score, 4),
                "logistics_cost_usd": round(wh["cost_per_ton"] * quantity_tons, 2),
            }
        )
    if not candidates:
        raise ValueError("no warehouse with sufficient inventory")
    best = min(candidates, key=lambda x: x["score"])
    return {"selected": best, "alternatives": sorted(candidates, key=lambda x: x["score"])[:5]}
