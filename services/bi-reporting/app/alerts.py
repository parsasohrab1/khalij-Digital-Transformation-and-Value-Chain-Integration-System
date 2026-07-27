"""هشدارهای هوشمند — حافظه + Postgres alerts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shared.db import dumps, pg_execute, pg_fetchall, pg_fetchone

_ALERTS: list[dict[str, Any]] = []
_HYDRATED = False


def _hydrate() -> None:
    global _HYDRATED
    if _HYDRATED:
        return
    rows = pg_fetchall(
        """
        SELECT id, alert_type, severity, message_fa, message_en, message_ar, subsidiary_code,
               metric_name, metric_value, threshold_value, acknowledged, acknowledged_by_name,
               raised_at, acknowledged_at, payload_json
        FROM alerts ORDER BY id DESC LIMIT 500
        """
    )
    loaded: list[dict[str, Any]] = []
    for row in rows:
        payload = row.get("payload_json") or {}
        if isinstance(payload, str):
            import json

            payload = json.loads(payload)
        if payload and payload.get("id"):
            loaded.append(payload)
            continue
        loaded.append(
            {
                "id": row["id"],
                "alert_type": row["alert_type"],
                "severity": row["severity"],
                "metric_name": row.get("metric_name"),
                "metric_value": row.get("metric_value"),
                "threshold_value": row.get("threshold_value"),
                "subsidiary_code": row.get("subsidiary_code"),
                "message_fa": row.get("message_fa"),
                "message_en": row.get("message_en"),
                "message_ar": row.get("message_ar"),
                "acknowledged": bool(row.get("acknowledged")),
                "acknowledged_by": row.get("acknowledged_by_name"),
                "acknowledged_at": row["acknowledged_at"].isoformat() if row.get("acknowledged_at") else None,
                "raised_at": row["raised_at"].isoformat() if row.get("raised_at") else None,
            }
        )
    if loaded:
        _ALERTS.clear()
        _ALERTS.extend(loaded)
    _HYDRATED = True


def _persist(alert: dict[str, Any]) -> None:
    pg_execute(
        """
        INSERT INTO alerts (
            id, alert_type, severity, message_fa, message_en, message_ar, subsidiary_code,
            metric_name, metric_value, threshold_value, acknowledged, acknowledged_by_name,
            payload_json, raised_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, COALESCE(%s::timestamptz, now())
        )
        ON CONFLICT (id) DO UPDATE SET
            acknowledged = EXCLUDED.acknowledged,
            acknowledged_by_name = EXCLUDED.acknowledged_by_name,
            acknowledged_at = CASE WHEN EXCLUDED.acknowledged THEN now() ELSE alerts.acknowledged_at END,
            payload_json = EXCLUDED.payload_json
        """,
        (
            alert["id"],
            alert["alert_type"],
            alert["severity"],
            alert.get("message_fa") or "",
            alert.get("message_en"),
            alert.get("message_ar"),
            alert.get("subsidiary_code"),
            alert.get("metric_name"),
            alert.get("metric_value"),
            alert.get("threshold_value"),
            bool(alert.get("acknowledged")),
            alert.get("acknowledged_by"),
            dumps(alert),
            alert.get("raised_at"),
        ),
    )


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
    _hydrate()
    deviation = abs(metric_value - threshold_value)
    deviation_pct = round(100 * deviation / max(abs(threshold_value), 1e-9), 2)
    next_id = max((a["id"] for a in _ALERTS), default=0) + 1
    # Prefer DB sequence if empty memory but DB has rows
    row = pg_fetchone("SELECT COALESCE(MAX(id), 0) AS max_id FROM alerts")
    if row:
        next_id = max(next_id, int(row["max_id"]) + 1)
    alert = {
        "id": next_id,
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
    _persist(alert)
    return alert


def list_alerts(
    *,
    limit: int = 50,
    severity: str | None = None,
    alert_type: str | None = None,
    only_active: bool = False,
) -> list[dict[str, Any]]:
    _hydrate()
    rows = _ALERTS
    if severity:
        rows = [a for a in rows if a["severity"] == severity]
    if alert_type:
        rows = [a for a in rows if a["alert_type"] == alert_type]
    if only_active:
        rows = [a for a in rows if not a.get("acknowledged")]
    return rows[:limit]


def acknowledge(alert_id: int, by: str = "operator") -> dict[str, Any] | None:
    _hydrate()
    for a in _ALERTS:
        if a["id"] == alert_id:
            a["acknowledged"] = True
            a["acknowledged_by"] = by
            a["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            _persist(a)
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
