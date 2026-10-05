"""AIS and GPS simulator/adapter for real-time shipment tracking."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

import numpy as np

# In-memory trail: shipment_number -> list[position]
_TRAILS: dict[str, list[dict[str, Any]]] = {}
_VESSELS: dict[str, dict[str, Any]] = {}  # mmsi -> last AIS ping


def register_vessel(mmsi: str, name: str, ship_type: str = "tanker") -> dict[str, Any]:
    vessel = {
        "mmsi": mmsi,
        "name": name,
        "ship_type": ship_type,
        "latitude": None,
        "longitude": None,
        "sog_knots": None,
        "cog_deg": None,
        "nav_status": "under_way",
        "updated_at": None,
    }
    _VESSELS[mmsi] = vessel
    return vessel


def ingest_ais(
    mmsi: str,
    latitude: float,
    longitude: float,
    sog_knots: float = 12.0,
    cog_deg: float = 90.0,
    nav_status: str = "under_way",
) -> dict[str, Any]:
    vessel = _VESSELS.get(mmsi) or register_vessel(mmsi, f"VESSEL-{mmsi}")
    vessel.update(
        {
            "latitude": latitude,
            "longitude": longitude,
            "sog_knots": sog_knots,
            "cog_deg": cog_deg,
            "nav_status": nav_status,
            "source": "AIS",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _VESSELS[mmsi] = vessel
    return vessel


def ingest_gps(
    shipment_number: str,
    latitude: float,
    longitude: float,
    speed_knots: float = 12.0,
    device_id: str | None = None,
) -> dict[str, Any]:
    point = {
        "lat": latitude,
        "lon": longitude,
        "speed_knots": speed_knots,
        "source": "GPS",
        "device_id": device_id or f"GPS-{shipment_number}",
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    _TRAILS.setdefault(shipment_number, []).insert(0, point)
    _TRAILS[shipment_number] = _TRAILS[shipment_number][:500]
    return point


def simulate_live_track(
    shipment_number: str,
    start_lat: float,
    start_lon: float,
    dest_lat: float,
    dest_lon: float,
    progress: float = 0.3,
    mmsi: str | None = None,
) -> dict[str, Any]:
    """Advance along the origin→destination route (0 to 1) and generate an AIS/GPS ping."""
    progress = float(np.clip(progress, 0.0, 1.0))
    lat = start_lat + (dest_lat - start_lat) * progress
    lon = start_lon + (dest_lon - start_lon) * progress
    # Small route noise
    rng = np.random.default_rng(abs(hash(shipment_number)) % (2**32))
    lat += float(rng.normal(0, 0.02))
    lon += float(rng.normal(0, 0.02))
    bearing = math.degrees(math.atan2(dest_lon - start_lon, dest_lat - start_lat)) % 360
    speed = float(10 + 4 * rng.random())

    gps = ingest_gps(shipment_number, lat, lon, speed)
    ais = None
    if mmsi:
        ais = ingest_ais(mmsi, lat, lon, speed, bearing)
    return {
        "shipment_number": shipment_number,
        "progress": progress,
        "latitude": lat,
        "longitude": lon,
        "speed_knots": speed,
        "heading_deg": round(bearing, 1),
        "gps": gps,
        "ais": ais,
        "fused_source": "AIS+GPS" if ais else "GPS",
    }


def get_trail(shipment_number: str, limit: int = 50) -> list[dict[str, Any]]:
    return _TRAILS.get(shipment_number, [])[:limit]


def get_vessel(mmsi: str) -> dict[str, Any] | None:
    return _VESSELS.get(mmsi)
