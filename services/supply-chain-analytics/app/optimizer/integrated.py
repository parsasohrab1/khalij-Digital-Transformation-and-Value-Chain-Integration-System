"""بهینه‌سازی یکپارچه حلقه‌بسته: تقاضا → قیمت → LP خوراک → تصمیم معامله."""
from __future__ import annotations

import time
import uuid
from typing import Any

import pulp

from shared.schemas import FeedstockAllocation, IntegratedOptimizationResult
from shared.settings import get_settings

from ..forecasting.trainer import train_and_forecast
from .trading_whatif import run_trading_whatif

settings = get_settings()

DEFAULT_UNITS = [
    {"code": "PU-BIPC-1", "max_feed_tons_day": 1200, "margin_per_ton_usd": 220, "product": "HDPE"},
    {"code": "PU-PID-1", "max_feed_tons_day": 2000, "margin_per_ton_usd": 180, "product": "PET"},
    {"code": "PU-ARPC-1", "max_feed_tons_day": 900, "margin_per_ton_usd": 250, "product": "HDPE"},
    {"code": "PU-NPC-1", "max_feed_tons_day": 800, "margin_per_ton_usd": 210, "product": "PP"},
]


def solve_feedstock_lp(
    available: float,
    units: list[dict],
    demand: dict[str, float] | None = None,
) -> tuple[list[FeedstockAllocation], float]:
    """LP با قید تقاضای پیش‌بینی‌شده (حلقه بسته)."""
    problem = pulp.LpProblem("holding_margin_maximize", pulp.LpMaximize)
    vars_ = {
        u["code"]: pulp.LpVariable(f"feed_{u['code']}", lowBound=0, upBound=float(u["max_feed_tons_day"]))
        for u in units
    }
    problem += pulp.lpSum(vars_[u["code"]] * float(u["margin_per_ton_usd"]) for u in units)
    problem += pulp.lpSum(vars_[u["code"]] for u in units) <= available, "feedstock_cap"

    # قید نرم تقاضا: مجموع تخصیص واحدهای هر محصول ≤ تقاضا * ضریب تبدیل تقریبی
    if demand:
        by_product: dict[str, list] = {}
        for u in units:
            by_product.setdefault(u.get("product", "HDPE"), []).append(u["code"])
        for product, codes in by_product.items():
            cap = float(demand.get(product, 1e9)) / max(1.0, settings.demand_forecast_horizon_days) * 1.5
            # تقاضا افقی است؛ ظرفیت روزانه را با میانگین روزانه تقاضا محدود می‌کنیم
            problem += pulp.lpSum(vars_[c] for c in codes) <= max(cap, 100.0), f"demand_{product}"

    problem.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=settings.lp_solver_time_limit_sec))
    allocations = [
        FeedstockAllocation(
            unit_code=u["code"],
            feedstock_tons=round(pulp.value(vars_[u["code"]]) or 0.0, 2),
            expected_margin_usd=round(
                (pulp.value(vars_[u["code"]]) or 0.0) * float(u["margin_per_ton_usd"]), 2
            ),
        )
        for u in units
    ]
    return allocations, round(sum(a.expected_margin_usd for a in allocations), 2)


def forecast_prices(oil_price: float, horizon_days: int) -> dict[str, float]:
    days_factor = 1.0 + 0.001 * (horizon_days / 30)
    return {
        "HDPE": round(900 + 5 * (oil_price - 75) * days_factor, 2),
        "PP": round(850 + 4 * (oil_price - 75) * days_factor, 2),
        "PET": round(880 + 3.5 * (oil_price - 75) * days_factor, 2),
        "feedstock": round(800 + 3 * (oil_price - 75) * days_factor, 2),
        "oil": round(oil_price, 2),
    }


def run_integrated_optimization(
    *,
    horizon_days: int = 90,
    available_feedstock_tons: float = 3500.0,
    oil_price_usd_bbl: float = 75.0,
    model_name: str | None = None,
    inventory_tons: float = 5000.0,
    what_if: dict[str, Any] | None = None,
) -> IntegratedOptimizationResult:
    t0 = time.perf_counter()
    demand_result = train_and_forecast(
        horizon_days=horizon_days, model_name=model_name, oil_price=oil_price_usd_bbl
    )
    demand = demand_result["demand_tons"]
    prices = forecast_prices(oil_price_usd_bbl, horizon_days)

    # اعمال سناریوی what-if روی قیمت/خوراک
    if what_if:
        if "oil_shock_pct" in what_if:
            shock = 1.0 + float(what_if["oil_shock_pct"]) / 100.0
            oil_price_usd_bbl *= shock
            prices = forecast_prices(oil_price_usd_bbl, horizon_days)
        if "feedstock_bonus_tons" in what_if:
            available_feedstock_tons += float(what_if["feedstock_bonus_tons"])

    allocations, lp_margin = solve_feedstock_lp(available_feedstock_tons, DEFAULT_UNITS, demand)

    sales_margin = 0.0
    for g, qty in demand.items():
        px = prices.get(g, prices["HDPE"])
        sales_margin += qty * (px - prices["feedstock"]) * 0.12
    sales_margin /= max(len(demand), 1)

    trading = run_trading_whatif(
        current_price=prices["HDPE"],
        oil_price=oil_price_usd_bbl,
        inventory_tons=inventory_tons,
        scenarios=what_if.get("trading_scenarios") if what_if else None,
    )

    holding_margin = round(lp_margin + sales_margin + float(trading.get("expected_pnl_usd", 0)), 2)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    return IntegratedOptimizationResult(
        holding_margin_usd=holding_margin,
        demand_forecast=demand,
        price_forecast=prices,
        feedstock_allocations=allocations,
        horizon_days=horizon_days,
        run_id=str(uuid.uuid4()),
        model_name=demand_result["model"],
        trading_decision=trading,
        closed_loop=True,
        latency_ms=latency_ms,
    )
