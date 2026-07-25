"""BI & Reporting Phase 4 — داشبورد تعاملی، گزارش سودآوری، هشدار هوشمند."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import redis
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from shared.i18n import bundle, t
from shared.logging_config import configure_logging
from shared.settings import get_settings

from .alerts import acknowledge, list_alerts, raise_alert, scan_budget_deviations
from .catalog import filters_catalog
from .kpis import build_kpis, build_timeseries, distribution_performance
from .reports import cost_margin_report

settings = get_settings()
configure_logging("bi-reporting", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - BI & Reporting Phase 4",
    description="Interactive Command Center analytics + profitability + smart alerts",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_redis: redis.Redis | None = None

ROLE_VIEWS = {
    "executive": ["dashboard", "cost", "alerts"],
    "analyst": ["dashboard", "cost", "distribution", "alerts", "optimize", "timeseries"],
    "logistics": ["dashboard", "distribution", "alerts"],
    "sales": ["dashboard", "alerts"],
    "admin": ["dashboard", "cost", "distribution", "alerts", "optimize", "timeseries"],
    "supervisor": ["dashboard", "cost", "distribution", "alerts"],
}


def get_redis() -> redis.Redis | None:
    global _redis
    try:
        if _redis is None:
            _redis = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.4)
            _redis.ping()
        return _redis
    except Exception:  # noqa: BLE001
        _redis = None
        return None


class AlertRequest(BaseModel):
    alert_type: str
    severity: str = "warning"
    metric_name: str
    metric_value: float
    threshold_value: float
    subsidiary_code: str | None = None
    region: str | None = None


class AckRequest(BaseModel):
    by: str = "operator"


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "bi-reporting",
        "phase": 4,
        "patent": "integrated-profitability-reporting",
    }


@app.get("/i18n/{locale}")
async def i18n_bundle(locale: str) -> dict:
    if locale not in {"fa", "en", "ar"}:
        raise HTTPException(status_code=400, detail="locale must be fa|en|ar")
    return {"locale": locale, "messages": bundle(locale)}


@app.get("/filters")
async def filters() -> dict:
    return filters_catalog()


@app.get("/roles/{role}/views")
async def role_views(role: str) -> dict:
    views = ROLE_VIEWS.get(role, ROLE_VIEWS["analyst"])
    return {"role": role, "views": views}


@app.get("/dashboard")
async def dashboard(
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    locale: str = Query(default="fa", pattern="^(fa|en|ar)$"),
    role: str = "analyst",
) -> dict:
    kpis = build_kpis(
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
        period=period,
    )
    holding_margin = None
    r = get_redis()
    if r is not None:
        try:
            raw = r.get("dvc:holding_margin_usd")
            holding_margin = float(raw) if raw is not None else None
        except Exception:  # noqa: BLE001
            pass

    return {
        "title": t("command_center_title", locale),
        "brand": t("brand", locale),
        "filters": {
            "subsidiary_code": subsidiary_code,
            "product_grade": product_grade,
            "region": region,
            "period": period,
        },
        "role": role,
        "views": ROLE_VIEWS.get(role, ROLE_VIEWS["analyst"]),
        "kpis": kpis,
        "labels": {
            "otif": t("kpi_otif", locale),
            "fill": t("kpi_fill", locale),
            "margin": t("kpi_margin", locale),
            "orders": t("kpi_orders", locale),
            "ships": t("kpi_ships", locale),
            "eta": t("kpi_eta", locale),
        },
        "holding_optimized_margin_usd": holding_margin,
        "active_alerts": len(list_alerts(only_active=True, limit=100)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/timeseries")
async def timeseries(
    metric: str = "operating_margin_percent",
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
) -> dict:
    return build_timeseries(
        metric=metric,
        period=period,
        subsidiary_code=subsidiary_code,
        product_grade=product_grade,
        region=region,
    )


@app.get("/reports/cost-per-ton")
async def cost_per_ton(
    subsidiary_code: str | None = None,
    unit_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    locale: str = "fa",
) -> dict:
    report = cost_margin_report(
        subsidiary_code=subsidiary_code,
        unit_code=unit_code,
        product_grade=product_grade,
        region=region,
    )
    report["title"] = t("cost_per_ton", locale)
    report["margin_title"] = t("margin_per_unit", locale)
    return report


@app.get("/reports/distribution")
async def distribution_report(
    subsidiary_code: str | None = None,
    region: str | None = None,
    period: str = Query(default="30d", pattern="^(7d|30d|90d)$"),
    locale: str = "fa",
) -> dict:
    data = distribution_performance(subsidiary_code=subsidiary_code, region=region, period=period)
    data["title"] = t("nav_distribution", locale)
    return data


@app.post("/alerts")
async def create_alert(body: AlertRequest) -> dict:
    return raise_alert(**body.model_dump())


@app.get("/alerts")
async def alerts(
    limit: int = 50,
    severity: str | None = None,
    alert_type: str | None = None,
    only_active: bool = False,
    locale: str = "fa",
) -> dict:
    rows = list_alerts(limit=limit, severity=severity, alert_type=alert_type, only_active=only_active)
    for a in rows:
        a["message"] = a.get(f"message_{locale}") or a.get("message_en")
    return {"title": t("alerts_title", locale), "alerts": rows}


@app.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(alert_id: int, body: AckRequest) -> dict:
    row = acknowledge(alert_id, body.by)
    if not row:
        raise HTTPException(status_code=404, detail="alert not found")
    return row


@app.post("/alerts/check-budgets")
async def check_budgets() -> dict:
    created = scan_budget_deviations()
    return {"created": len(created), "alerts": created}
