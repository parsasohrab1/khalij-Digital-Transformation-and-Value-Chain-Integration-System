"""Standardization of HS code and unit of measurement to tons (FR-DATA-03)."""
from __future__ import annotations

from shared.events import NormalizedProductRecord

from .connectors.base import RawRecord

# Convert to tons
UOM_TO_TON = {
    "ton": 1.0,
    "t": 1.0,
    "mt": 1.0,
    "kg": 0.001,
    "kilogram": 0.001,
    "lb": 0.000453592,
    "lbs": 0.000453592,
    "pound": 0.000453592,
}

GRADE_TO_HS = {
    "HDPE": "390120",
    "LDPE": "390110",
    "LLDPE": "390190",
    "PP": "390210",
    "PET": "390760",
}

GRADE_TO_INTERNAL = {
    "HDPE": "POLY-HDPE-01",
    "LDPE": "POLY-LDPE-01",
    "LLDPE": "POLY-LLDPE-01",
    "PP": "POLY-PP-01",
    "PET": "POLY-PET-01",
}


def to_tons(quantity: float, uom: str) -> float:
    factor = UOM_TO_TON.get(uom.strip().lower())
    if factor is None:
        raise ValueError(f"unsupported uom: {uom}")
    return round(quantity * factor, 6)


def normalize_record(raw: RawRecord, subsidiary_code: str) -> NormalizedProductRecord:
    grade = (raw.grade or "HDPE").upper()
    hs = raw.hs_code or GRADE_TO_HS.get(grade, "390120")
    internal = GRADE_TO_INTERNAL.get(grade, f"POLY-{grade}-01")
    tons = to_tons(raw.quantity, raw.uom)
    return NormalizedProductRecord(
        source_sku=raw.source_sku,
        internal_code=internal,
        hs_code=hs,
        grade=grade,
        quantity_raw=raw.quantity,
        uom_raw=raw.uom,
        quantity_tons=tons,
        subsidiary_code=subsidiary_code,
    )


def normalize_batch(records: list[RawRecord], subsidiary_code: str) -> list[NormalizedProductRecord]:
    out: list[NormalizedProductRecord] = []
    for r in records:
        try:
            out.append(normalize_record(r, subsidiary_code))
        except ValueError:
            continue
    return out
