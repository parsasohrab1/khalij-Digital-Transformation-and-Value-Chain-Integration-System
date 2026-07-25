"""محاسبه ETA با آب‌وهوا + ترافیک بندر + سرعت واقعی AIS/GPS."""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from .ports import get_port_live
from .weather import estimate_weather, region_for_route


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return (2 * r * math.asin(math.sqrt(a))) / 1.852


def compute_eta(
    *,
    origin_port: str,
    latitude: float,
    longitude: float,
    speed_knots: float,
    destination: str,
    destination_lat: float,
    destination_lon: float,
    weather_override_hours: float | None = None,
) -> dict[str, Any]:
    port = get_port_live(origin_port)
    region = region_for_route(origin_port, destination)
    weather = estimate_weather(region)
    weather_delay = weather_override_hours if weather_override_hours is not None else weather["delay_hours"]

    distance_nm = haversine_nm(latitude, longitude, destination_lat, destination_lon)
    speed = max(float(speed_knots or 10.0), 1.0)
    steaming_hours = distance_nm / speed
    congestion_hours = float(port["congestion_hours"])

    total_hours = steaming_hours + congestion_hours + float(weather_delay)
    eta_days = float(np.clip(round(total_hours / 24.0, 1), 0.5, 45))

    return {
        "eta_days": eta_days,
        "eta_hours": round(total_hours, 1),
        "breakdown": {
            "distance_nm": round(distance_nm, 1),
            "steaming_hours": round(steaming_hours, 1),
            "port_congestion_hours": round(congestion_hours, 1),
            "weather_delay_hours": round(float(weather_delay), 1),
            "ships_in_port": port["ships_in_port"],
            "berth_occupancy_pct": port["berth_occupancy_pct"],
        },
        "weather": weather,
        "port": {
            "key": origin_port,
            "code": port["code"],
            "pmo_code": port["pmo_code"],
            "status": port["status"],
        },
    }
