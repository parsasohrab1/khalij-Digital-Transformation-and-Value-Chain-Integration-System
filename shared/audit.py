"""Recording security and operational events (Audit Log) — memory + Postgres."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from shared.db import dumps, pg_execute, pg_fetchall
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
    pg_execute(
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
            dumps(details or {}),
        ),
    )
    return entry


def list_audit(limit: int = 100) -> list[dict[str, Any]]:
    rows = pg_fetchall(
        """
        SELECT action, actor, resource, outcome, ip, details_json, created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    if rows:
        out = []
        for r in rows:
            details = r.get("details_json") or {}
            if isinstance(details, str):
                details = json.loads(details)
            out.append(
                {
                    "ts": r["created_at"].isoformat() if r.get("created_at") else None,
                    "action": r["action"],
                    "actor": r["actor"],
                    "resource": r["resource"],
                    "outcome": r["outcome"],
                    "ip": r["ip"],
                    "details": details,
                }
            )
        return out
    return _MEMORY_AUDIT[:limit]
