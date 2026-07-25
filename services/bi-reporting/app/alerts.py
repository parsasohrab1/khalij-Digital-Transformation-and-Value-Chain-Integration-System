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


def scan_budget_deviations() -> list[dict[str, Any]]:
    checks = [
        ("production", "production_plan_tons", 950.0, 1000.0, "warning", "BIPC", "Khuzestan"),
        ("sales", "sales_plan_usd", 1.8e6, 2.0e6, "warning", "NPC", "Tehran"),
        ("budget", "opex_usd", 1.15e6, 1.0e6, "critical", "PIDMCO", "Assaluyeh"),
        ("logistics", "avg_eta_days", 9.5, 7.0, "warning", "BIPC", "Hormozgan"),
    ]
    created = []
    for alert_type, metric, value, threshold, severity, sub, region in checks:
        breached = (severity == "critical" and value > threshold) or (
            severity == "warning" and abs(value - threshold) / threshold > 0.05
        )
        if breached:
            created.append(
                raise_alert(
                    alert_type=alert_type,
                    severity=severity,
                    metric_name=metric,
                    metric_value=value,
                    threshold_value=threshold,
                    subsidiary_code=sub,
                    region=region,
                )
            )
    return created
