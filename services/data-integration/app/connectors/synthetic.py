"""Extraction from sources with fallback to synthetic data when the driver/DB is unavailable."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import RawRecord


def load_synthetic_oltp(limit: int = 500, data_path: str | None = None) -> list[RawRecord]:
    """Simulate extraction from a subsidiary OLTP with synthetic CSV."""
    candidates = [
        Path(data_path) if data_path else None,
        Path("data/digital_value_chain_data_10k.csv"),
        Path("/app/data/digital_value_chain_data_10k.csv"),
    ]
    path = next((p for p in candidates if p and p.exists()), None)
    if path is None:
        # At least one batch of fake records
        now = datetime.utcnow()
        return [
            RawRecord(
                source_sku=f"SKU-HDPE-{i}",
                grade="HDPE",
                quantity=100 + i * 3,
                uom="kg" if i % 2 == 0 else "ton",
                hs_code="390120",
                warehouse_code=["WH-BND", "WH-THR", "WH-ASL"][i % 3],
                oil_price=75.0,
                price_hdpe=920.0,
                price_pp=860.0,
                feedstock_price=810.0,
                timestamp=now,
            )
            for i in range(min(limit, 20))
        ]

    rows: list[RawRecord] = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            grade = row.get("product_type", "HDPE")
            hs_map = {"HDPE": "390120", "LDPE": "390110", "LLDPE": "390190", "PP": "390210", "PET": "390760"}
            qty = float(row.get("order_quantity_tons", 50))
            # We convert half of the records to kg so that UOM normalization is tested
            if i % 3 == 0:
                quantity, uom = qty * 1000, "kg"
            elif i % 3 == 1:
                quantity, uom = qty * 2204.62, "lb"
            else:
                quantity, uom = qty, "ton"
            rows.append(
                RawRecord(
                    source_sku=f"SKU-{grade}-{i}",
                    grade=grade,
                    quantity=quantity,
                    uom=uom,
                    hs_code=hs_map.get(grade),
                    warehouse_code=["WH-BND", "WH-THR", "WH-ASL"][i % 3],
                    oil_price=float(row.get("oil_price_usd_bbl", 75)),
                    price_hdpe=float(row.get("price_hdpe_usd_ton", 900)),
                    price_pp=float(row.get("price_pp_usd_ton", 850)),
                    feedstock_price=float(row.get("feedstock_price_usd_ton", 800)),
                    timestamp=datetime.fromisoformat(row["timestamp"]) if row.get("timestamp") else datetime.utcnow(),
                    extra={"orders_received": row.get("orders_received")},
                )
            )
    return rows


def connection_status(ok: bool, detail: str, mode: str) -> dict[str, Any]:
    return {"ok": ok, "detail": detail, "mode": mode}
