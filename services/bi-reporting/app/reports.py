"""Cost per ton and unit profit margin report (adjusted from CSV)."""
from __future__ import annotations

from typing import Any

import numpy as np

from .catalog import UNIT_META
from .kpis import csv_adjusted_unit_costs


def cost_margin_report(
    *,
    subsidiary_code: str | None = None,
    unit_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
) -> dict[str, Any]:
    cost_base = csv_adjusted_unit_costs(
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
        period=period,
    )
    rows = []
    for code, costs in cost_base.items():
        meta = UNIT_META[code]
        if unit_code and code != unit_code:
            continue
        if subsidiary_code and meta["subsidiary_code"] != subsidiary_code:
            continue
        if region and meta["region"] != region:
            continue
        if product_grade and meta["product"] != product_grade:
            continue
        total_cost = costs["feedstock"] + costs["energy"] + costs["logistics"] + costs["overhead"]
        margin = costs["revenue"] - total_cost
        margin_pct = round(100 * margin / costs["revenue"], 2) if costs["revenue"] else 0.0
        rows.append(
            {
                "unit_code": code,
                "subsidiary_code": meta["subsidiary_code"],
                "region": meta["region"],
                "product": meta["product"],
                "cost_per_ton_usd": round(total_cost, 2),
                "breakdown": costs,
                "revenue_per_ton_usd": costs["revenue"],
                "margin_per_ton_usd": round(margin, 2),
                "margin_percent": margin_pct,
            }
        )
    return {
        "filters": {
            "subsidiary_code": subsidiary_code,
            "unit_code": unit_code,
            "product_grade": product_grade,
            "region": region,
            "period": period,
        },
        "units": rows,
        "holding_avg_cost_per_ton": round(float(np.mean([r["cost_per_ton_usd"] for r in rows])), 2) if rows else 0,
        "holding_avg_margin_percent": round(float(np.mean([r["margin_percent"] for r in rows])), 2) if rows else 0,
        "holding_avg_margin_per_ton": round(float(np.mean([r["margin_per_ton_usd"] for r in rows])), 2) if rows else 0,
        "data_source": "csv_adjusted",
    }
