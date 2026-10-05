"""Trading optimization with what-if scenarios (FR-ML-03)."""
from __future__ import annotations

from typing import Any


def _price_path(oil: float, days: int = 14) -> list[float]:
    base = 900 + 5 * (oil - 75)
    path = []
    for d in range(days):
        # Simple sinusoidal fluctuation
        import math

        path.append(round(base + 15 * math.sin(d / 3) + 5 * math.cos(d / 5), 2))
    return path


def evaluate_scenario(
    name: str,
    current_price: float,
    forecast_prices: list[float],
    inventory_tons: float,
    action: str,
) -> dict[str, Any]:
    peak = max(forecast_prices)
    trough = min(forecast_prices)
    if action == "buy":
        pnl = (peak - current_price) * min(inventory_tons * 0.1, 500)
        decision = "buy"
    elif action == "sell":
        pnl = (current_price - trough) * min(inventory_tons * 0.1, 500)
        decision = "sell"
    else:
        if current_price <= trough * 1.02:
            decision, pnl = "buy", (peak - current_price) * min(inventory_tons * 0.1, 500)
        elif current_price >= peak * 0.98:
            decision, pnl = "sell", (current_price - trough) * min(inventory_tons * 0.1, 500)
        else:
            decision, pnl = "hold", 0.0
    return {
        "scenario": name,
        "decision": decision,
        "expected_pnl_usd": round(pnl, 2),
        "forecast_peak": peak,
        "forecast_trough": trough,
    }


def run_trading_whatif(
    *,
    current_price: float,
    oil_price: float,
    inventory_tons: float,
    scenarios: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    base_path = _price_path(oil_price)
    default_scenarios = scenarios or [
        {"name": "base", "action": "auto", "oil_delta": 0},
        {"name": "oil_spike", "action": "auto", "oil_delta": 8},
        {"name": "oil_drop", "action": "auto", "oil_delta": -6},
        {"name": "force_sell", "action": "sell", "oil_delta": 0},
    ]

    results = []
    for sc in default_scenarios:
        path = _price_path(oil_price + float(sc.get("oil_delta", 0)))
        results.append(
            evaluate_scenario(
                sc.get("name", "unnamed"),
                current_price,
                path,
                inventory_tons,
                sc.get("action", "auto"),
            )
        )

    best = max(results, key=lambda r: r["expected_pnl_usd"])
    return {
        "decision": best["decision"],
        "expected_pnl_usd": best["expected_pnl_usd"],
        "selected_scenario": best["scenario"],
        "scenarios": results,
        "base_forecast_prices": base_path,
        "inventory_tons": inventory_tons,
    }
