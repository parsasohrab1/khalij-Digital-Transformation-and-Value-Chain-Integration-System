"""هشدارهای هوشمند انحراف تولید/فروش/بودجه با تأیید."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

_ALERTS: list[dict[str, Any]] = []


def raise_alert(
    *,
    alert_type: str,
    severity: str,
    metric_name: str,
    metric_value: float,
    threshold_value: float,
    subsidiary_code: str | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    deviation = abs(metric_value - threshold_value)
    deviation_pct = round(100 * deviation / max(abs(threshold_value), 1e-9), 2)
    alert = {
        "id": (max((a["id"] for a in _ALERTS), default=0) + 1),
        "alert_type": alert_type,
        "severity": severity,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "threshold_value": threshold_value,
        "deviation_pct": deviation_pct,
        "subsidiary_code": subsidiary_code,
        "region": region,
        "message_fa": (
            f"انحراف {alert_type}: {metric_name}={metric_value} "
            f"(آستانه {threshold_value}، Δ%{deviation_pct})"
        ),
        "message_en": (
            f"{alert_type} deviation: {metric_name}={metric_value} "
            f"(threshold {threshold_value}, Δ%{deviation_pct})"
        ),
        "message_ar": (
            f"انحراف {alert_type}: {metric_name}={metric_value} "
            f"(الحد {threshold_value})"
        ),
        "acknowledged": False,
        "acknowledged_by": None,
        "acknowledged_at": None,
        "raised_at": datetime.now(timezone.utc).isoformat(),
    }
    _ALERTS.insert(0, alert)
    return alert


def list_alerts(
    *,
    limit: int = 50,
    severity: str | None = None,
    alert_type: str | None = None,
    only_active: bool = False,
) -> list[dict[str, Any]]:
    rows = _ALERTS
    if severity:
        rows = [a for a in rows if a["severity"] == severity]
    if alert_type:
        rows = [a for a in rows if a["alert_type"] == alert_type]
    if only_active:
        rows = [a for a in rows if not a.get("acknowledged")]
    return rows[:limit]


def acknowledge(alert_id: int, by: str = "operator") -> dict[str, Any] | None:
    for a in _ALERTS:
        if a["id"] == alert_id:
            a["acknowledged"] = True
            a["acknowledged_by"] = by
            a["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            return a
    return None


def scan_budget_deviations(
    *,
    kpis: dict[str, Any] | None = None,
    subsidiary_code: str | None = None,
    region: str | None = None,
) -> list[dict[str, Any]]:
    kpis = kpis or {}
    checks = [
        (
            "otif",
            "otif_percent",
            float(kpis.get("otif_percent", 88.0)),
            90.0,
            "warning" if float(kpis.get("otif_percent", 88.0)) < 90 else "info",
            subsidiary_code or "BIPC",
            region or "Khuzestan",
        ),
        (
            "margin",
            "operating_margin_percent",
            float(kpis.get("operating_margin_percent", 18.0)),
            20.0,
            "warning" if float(kpis.get("operating_margin_percent", 18.0)) < 20 else "info",
            subsidiary_code or "NPC",
            region or "Tehran",
        ),
        (
            "logistics",
            "avg_eta_days",
            float(kpis.get("avg_eta_days", 8.0)),
            7.0,
            "warning" if float(kpis.get("avg_eta_days", 8.0)) > 7 else "info",
            subsidiary_code or "PIDMCO",
            region or "Assaluyeh",
        ),
        (
            "fill",
            "warehouse_fill_rate_percent",
            float(kpis.get("warehouse_fill_rate_percent", 70.0)),
            75.0,
            "warning" if float(kpis.get("warehouse_fill_rate_percent", 70.0)) < 75 else "info",
            subsidiary_code or "ARPC",
            region or "Assaluyeh",
        ),
    ]
    created = []
    for alert_type, metric, value, threshold, severity, sub, reg in checks:
        if severity == "info":
            continue
        created.append(
            raise_alert(
                alert_type=alert_type,
                severity=severity,
                metric_name=metric,
                metric_value=round(value, 2),
                threshold_value=threshold,
                subsidiary_code=sub,
                region=reg,
            )
        )
    if not created:
        created.append(
            raise_alert(
                alert_type="budget",
                severity="info",
                metric_name="holding_health",
                metric_value=1.0,
                threshold_value=1.0,
                subsidiary_code=subsidiary_code,
                region=region,
            )
        )
    return created
