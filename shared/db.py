"""PostgreSQL helpers — best-effort persistence with memory fallback."""
from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Iterator

from shared.settings import get_settings

logger = logging.getLogger(__name__)


def pg_dsn() -> str:
    return get_settings().postgres_dsn.replace("postgresql+psycopg2", "postgresql")


@contextmanager
def pg_cursor() -> Iterator[Any]:
    import psycopg2
    import psycopg2.extras

    conn = psycopg2.connect(pg_dsn())
    try:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                yield cur
    finally:
        conn.close()


def pg_execute(sql: str, params: tuple | list | None = None) -> bool:
    try:
        with pg_cursor() as cur:
            cur.execute(sql, params or ())
        return True
    except Exception as exc:  # noqa: BLE001
        logger.debug("pg_execute skipped: %s", exc)
        return False


def pg_fetchall(sql: str, params: tuple | list | None = None) -> list[dict[str, Any]]:
    try:
        with pg_cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.debug("pg_fetchall skipped: %s", exc)
        return []


def pg_fetchone(sql: str, params: tuple | list | None = None) -> dict[str, Any] | None:
    rows = pg_fetchall(sql, params)
    return rows[0] if rows else None


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)
