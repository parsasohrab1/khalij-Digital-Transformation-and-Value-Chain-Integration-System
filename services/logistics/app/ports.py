"""بنادر ایران — کد PMO، اسکله، ترافیک لحظه‌ای (بومی‌سازی ثبت اختراع)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

IRAN_PORTS: dict[str, dict[str, Any]] = {
    "BandarAbbas": {
        "lat": 27.1832,
        "lon": 56.2666,
        "code": "IRBND",
        "pmo_code": "BND",
        "name_fa": "بندر شهید رجایی / بندرعباس",
        "name_en": "Bandar Abbas / Shahid Rajaee",
        "base_congestion_hours": 18,
        "berths": 12,
        "customs_office": "Hormozgan Customs",
    },
    "Assaluyeh": {
        "lat": 27.4761,
        "lon": 52.6070,
        "code": "IRASL",
        "pmo_code": "ASL",
        "name_fa": "بندر عسلویه",
        "name_en": "Assaluyeh Port",
        "base_congestion_hours": 12,
        "berths": 8,
        "customs_office": "Bushehr Customs - Assaluyeh",
    },
    "Bushehr": {
        "lat": 28.9234,
        "lon": 50.8203,
        "code": "IRBUZ",
        "pmo_code": "BUZ",
        "name_fa": "بندر بوشهر",
        "name_en": "Bushehr Port",
        "base_congestion_hours": 10,
        "berths": 6,
        "customs_office": "Bushehr Customs",
    },
    "ImamKhomeini": {
        "lat": 30.4333,
        "lon": 49.0667,
        "code": "IRIKH",
        "pmo_code": "IKH",
        "name_fa": "بندر امام خمینی",
        "name_en": "Imam Khomeini Port",
        "base_congestion_hours": 24,
        "berths": 15,
        "customs_office": "Khuzestan Customs",
    },
    "Chabahar": {
        "lat": 25.2919,
        "lon": 60.6430,
        "code": "IRZBR",
        "pmo_code": "ZBR",
        "name_fa": "بندر چابهار",
        "name_en": "Chabahar Port",
        "base_congestion_hours": 8,
        "berths": 5,
        "customs_office": "Sistan & Baluchestan Customs",
    },
}

_PORT_LIVE: dict[str, dict[str, Any]] = {}


def refresh_port_traffic(port_key: str, seed: int | None = None) -> dict[str, Any]:
    if port_key not in IRAN_PORTS:
        raise KeyError(port_key)
    rng = np.random.default_rng(seed)
    base = IRAN_PORTS[port_key]
    ships = int(rng.integers(0, min(8, base["berths"] + 1)))
    congestion = float(base["base_congestion_hours"] * (1.0 + 0.15 * ships / max(base["berths"], 1)))
    occupancy = round(100.0 * ships / max(base["berths"], 1), 1)
    live = {
        **base,
        "port_key": port_key,
        "ships_in_port": ships,
        "berth_occupancy_pct": occupancy,
        "congestion_hours": round(congestion, 1),
        "status": "congested" if occupancy > 70 else "normal",
        "pmo_feed": "pmo.ir/simulated",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _PORT_LIVE[port_key] = live
    return live


def get_port_live(port_key: str) -> dict[str, Any]:
    return _PORT_LIVE.get(port_key) or refresh_port_traffic(port_key)


def list_ports_live() -> list[dict[str, Any]]:
    return [get_port_live(k) for k in IRAN_PORTS]
