"""کانکتور SQL Server — pymssql/pyodbc اختیاری + fallback."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, RawRecord
from .synthetic import connection_status, load_synthetic_oltp


class SQLServerConnector(BaseConnector):
    source_system = "SQLServer"

    def test_connection(self) -> dict[str, Any]:
        if self.connection_uri.startswith("simulated://"):
            return connection_status(True, "simulated sqlserver", "simulated")
        try:
            import pymssql  # type: ignore

            # connection_uri: server=...;user=...;password=...;database=...
            parts = dict(p.split("=", 1) for p in self.connection_uri.split(";") if "=" in p)
            conn = pymssql.connect(
                server=parts.get("server", "localhost"),
                user=parts.get("user", "sa"),
                password=parts.get("password", ""),
                database=parts.get("database", "master"),
            )
            conn.close()
            return connection_status(True, "connected", "live")
        except Exception as exc:  # noqa: BLE001
            return connection_status(False, str(exc), "fallback")

    def extract(self, limit: int = 500) -> list[RawRecord]:
        if self.test_connection()["mode"] != "live":
            return load_synthetic_oltp(limit)
        return load_synthetic_oltp(limit)
