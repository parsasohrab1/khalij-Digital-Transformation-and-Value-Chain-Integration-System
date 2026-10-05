"""Oracle connector — live connection if oracledb is installed, otherwise synthetic fallback."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, RawRecord
from .synthetic import connection_status, load_synthetic_oltp


class OracleConnector(BaseConnector):
    source_system = "Oracle"

    def test_connection(self) -> dict[str, Any]:
        if self.connection_uri.startswith("simulated://"):
            return connection_status(True, "simulated oracle", "simulated")
        try:
            import oracledb  # type: ignore

            # Example connection_uri: user/pass@host:1521/service
            conn = oracledb.connect(self.connection_uri)
            conn.close()
            return connection_status(True, "connected", "live")
        except Exception as exc:  # noqa: BLE001
            return connection_status(False, str(exc), "fallback")

    def extract(self, limit: int = 500) -> list[RawRecord]:
        status = self.test_connection()
        if status["mode"] != "live":
            return load_synthetic_oltp(limit)
        # Live path: SELECT from entity with bind limit
        try:
            import oracledb  # type: ignore

            conn = oracledb.connect(self.connection_uri)
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {self.source_entity} FETCH FIRST :lim ROWS ONLY", lim=limit)
            cols = [d[0].lower() for d in cur.description]
            rows = []
            for tup in cur.fetchall():
                r = dict(zip(cols, tup))
                rows.append(
                    RawRecord(
                        source_sku=str(r.get("sku") or r.get("item_code") or "ORACLE-SKU"),
                        grade=str(r.get("grade") or "HDPE"),
                        quantity=float(r.get("quantity") or 0),
                        uom=str(r.get("uom") or "ton"),
                        hs_code=r.get("hs_code"),
                    )
                )
            cur.close()
            conn.close()
            return rows or load_synthetic_oltp(limit)
        except Exception:  # noqa: BLE001
            return load_synthetic_oltp(limit)
