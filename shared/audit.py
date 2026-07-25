"""ثبت رخدادهای امنیتی و عملیاتی (Audit Log) برای انطباق و ثبت اختراع."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from shared.settings import get_settings

logger = logging.getLogger("audit")
settings = get_settings()

_MEMORY_AUDIT: list[dict[str, Any]] = []


def audit(
    *,
    action: str,
    actor: str = "system",
    resource: str | None = None,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
    ip: str | None = None,
) -> dict[str, Any]:
    if not settings.audit_log_enabled:
        return {}
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "resource": resource,
        "outcome": outcome,
        "ip": ip,
        "details": details or {},
    }
    _MEMORY_AUDIT.insert(0, entry)
    del _MEMORY_AUDIT[5000:]
    logger.info("AUDIT %s", json.dumps(entry, ensure_ascii=False, default=str))

    # best-effort DB persist
    try:
        import psycopg2

        dsn = settings.postgres_dsn.replace("postgresql+psycopg2", "postgresql")
        with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_logs (action, actor, resource, outcome, ip, details_json)
                VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                """,
                (
                    action,
                    actor,
                    resource,
                    outcome,
                    ip,
                    json.dumps(details or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
    except Exception:  # noqa: BLE001
        pass
    return entry


def list_audit(limit: int = 100) -> list[dict[str, Any]]:
    return _MEMORY_AUDIT[:limit]
