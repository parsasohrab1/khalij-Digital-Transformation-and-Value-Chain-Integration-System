"""کانکتور PostgreSQL واقعی + fallback سنتتیک."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, RawRecord
from .synthetic import connection_status, load_synthetic_oltp


class PostgreSQLConnector(BaseConnector):
    source_system = "PostgreSQL"

    def test_connection(self) -> dict[str, Any]:
        if self.connection_uri.startswith("simulated://"):
            return connection_status(True, "simulated postgres", "simulated")
        try:
            import psycopg2

            with psycopg2.connect(self.connection_uri) as conn, conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            return connection_status(True, "connected", "live")
        except Exception as exc:  # noqa: BLE001
            return connection_status(False, str(exc), "fallback")

    def extract(self, limit: int = 500) -> list[RawRecord]:
        status = self.test_connection()
        if status["mode"] != "live":
            return load_synthetic_oltp(limit)

        import psycopg2
        import psycopg2.extras

        sql = f"""
            SELECT * FROM {self.source_entity}
            ORDER BY 1 DESC
            LIMIT %s
        """
        rows: list[RawRecord] = []
        with psycopg2.connect(self.connection_uri) as conn, conn.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        ) as cur:
            cur.execute(sql, (limit,))
            for r in cur.fetchall():
                rows.append(
                    RawRecord(
                        source_sku=str(r.get("sku") or r.get("internal_code") or r.get("id")),
                        grade=str(r.get("grade") or r.get("product_type") or "HDPE"),
                        quantity=float(r.get("quantity") or r.get("qty") or 0),
                        uom=str(r.get("uom") or "ton"),
                        hs_code=r.get("hs_code"),
                        warehouse_code=r.get("warehouse_code"),
                        timestamp=r.get("timestamp") or r.get("created_at"),
                    )
                )
        return rows or load_synthetic_oltp(limit)
