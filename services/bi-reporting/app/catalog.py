"""کاتالوگ فیلترهای داشبورد هلدینگ."""
from __future__ import annotations

SUBSIDIARIES = [
    {"code": "NPC", "region": "Tehran", "name_fa": "شرکت ملی صنایع پتروشیمی", "name_en": "NPC"},
    {"code": "BIPC", "region": "Khuzestan", "name_fa": "پتروشیمی بندرامام", "name_en": "BIPC"},
    {"code": "PIDMCO", "region": "Assaluyeh", "name_fa": "پتروشیمی پردیس", "name_en": "Pardis"},
    {"code": "ARPC", "region": "Assaluyeh", "name_fa": "پتروشیمی آرین", "name_en": "Aryan"},
]

PRODUCTS = ["HDPE", "LDPE", "LLDPE", "PP", "PET"]
REGIONS = ["Tehran", "Khuzestan", "Assaluyeh", "Hormozgan"]
PERIODS = {"7d": 7, "30d": 30, "90d": 90}

UNIT_META = {
    "PU-BIPC-1": {"subsidiary_code": "BIPC", "region": "Khuzestan", "product": "HDPE"},
    "PU-PID-1": {"subsidiary_code": "PIDMCO", "region": "Assaluyeh", "product": "PET"},
    "PU-ARPC-1": {"subsidiary_code": "ARPC", "region": "Assaluyeh", "product": "HDPE"},
    "PU-NPC-1": {"subsidiary_code": "NPC", "region": "Tehran", "product": "PP"},
}

UNIT_COST_BASE = {
    "PU-BIPC-1": {"feedstock": 820, "energy": 95, "logistics": 48, "overhead": 35, "revenue": 1180},
    "PU-PID-1": {"feedstock": 760, "energy": 110, "logistics": 42, "overhead": 40, "revenue": 1050},
    "PU-ARPC-1": {"feedstock": 840, "energy": 88, "logistics": 50, "overhead": 38, "revenue": 1250},
    "PU-NPC-1": {"feedstock": 800, "energy": 92, "logistics": 55, "overhead": 36, "revenue": 1120},
}


def filters_catalog() -> dict:
    return {
        "subsidiaries": SUBSIDIARIES,
        "products": PRODUCTS,
        "regions": REGIONS,
        "periods": list(PERIODS.keys()),
    }
