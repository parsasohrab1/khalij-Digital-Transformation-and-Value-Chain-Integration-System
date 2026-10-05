"""Weather model for ETA delay (Persian Gulf / Oman Sea)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import numpy as np

SEA_REGIONS = {
    "persian_gulf": {"wave_m_base": 1.2, "wind_kt_base": 18},
    "strait_of_hormuz": {"wave_m_base": 1.8, "wind_kt_base": 22},
    "oman_sea": {"wave_m_base": 2.0, "wind_kt_base": 24},
}


def estimate_weather(
    region: str = "persian_gulf",
    season_month: int | None = None,
) -> dict[str, Any]:
    month = season_month or datetime.now(timezone.utc).month
    base = SEA_REGIONS.get(region, SEA_REGIONS["persian_gulf"])
    # Persian Gulf summer/winter
    monsoon = 1.35 if month in {6, 7, 8, 12, 1} else 1.0
    rng = np.random.default_rng(month * 17)
    wave_m = float(base["wave_m_base"] * monsoon * (0.85 + 0.3 * rng.random()))
    wind_kt = float(base["wind_kt_base"] * monsoon * (0.85 + 0.3 * rng.random()))
    visibility_nm = float(max(2.0, 12.0 - 0.2 * wind_kt + rng.normal(0, 0.5)))

    # Delay: wave>2m or wind>25kt
    delay_hours = 0.0
    if wave_m > 2.0:
        delay_hours += (wave_m - 2.0) * 6
    if wind_kt > 25:
        delay_hours += (wind_kt - 25) * 0.8
    if visibility_nm < 3:
        delay_hours += 4

    severity = "severe" if delay_hours >= 12 else "moderate" if delay_hours >= 4 else "calm"
    return {
        "region": region,
        "wave_height_m": round(wave_m, 2),
        "wind_knots": round(wind_kt, 1),
        "visibility_nm": round(visibility_nm, 1),
        "delay_hours": round(delay_hours, 1),
        "severity": severity,
        "source": "weather-sim/persian-gulf",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def region_for_route(origin_port: str, destination: str) -> str:
    dest = destination.lower()
    if origin_port in {"Chabahar"} or "india" in dest or "china" in dest:
        return "oman_sea"
    if origin_port in {"BandarAbbas"} or "jebel" in dest or "fujairah" in dest:
        return "strait_of_hormuz"
    return "persian_gulf"
