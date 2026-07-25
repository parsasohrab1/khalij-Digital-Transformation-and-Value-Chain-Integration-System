"""ثبت نسب‌شناسی داده (Data Lineage) برای اثبات مالکیت دامنه Data Mesh."""
from __future__ import annotations

import json
import logging
from typing import Any

import psycopg2
import psycopg2.extras

from shared.events import SCHEMA_VERSION
from shared.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_MEMORY_LINEAGE: list[dict[str, Any]] = []


def _pg_dsn() -> str:
    return settings.postgres_dsn.replace("postgresql+psycopg2", "postgresql")


def record_lineage(
    *,
    source_system: str,
    source_entity: str,
    domain_code: str,
    target_topic: str,
    target_table: str,
    transform_note: str,
    records_count: int = 0,
    extra: dict[str, Any] | None = None,
) -> str | None:
    entry = {
        "source_system": source_system,
        "source_entity": source_entity,
        "domain_code": domain_code,
        "target_topic": target_topic,
        "target_table": target_table,
        "transform_note": transform_note,
        "records_count": records_count,
        "schema_version": SCHEMA_VERSION,
        "payload_json": extra or {},
    }
    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_lineage
                    (source_system, source_entity, domain_code, target_topic, target_table,
                     transform_note, records_count, schema_version, payload_json)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb)
                RETURNING id
                """,
                (
                    source_system,
                    source_entity,
                    domain_code,
                    target_topic,
                    target_table,
                    transform_note,
                    records_count,
                    SCHEMA_VERSION,
                    json.dumps(extra or {}),
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return str(row[0]) if row else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("lineage DB write failed, using memory: %s", exc)
        entry["id"] = f"mem-{len(_MEMORY_LINEAGE)+1}"
        _MEMORY_LINEAGE.insert(0, entry)
        return entry["id"]


def list_lineage(limit: int = 50) -> list[dict[str, Any]]:
    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM data_lineage ORDER BY recorded_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception:  # noqa: BLE001
        return _MEMORY_LINEAGE[:limit]
