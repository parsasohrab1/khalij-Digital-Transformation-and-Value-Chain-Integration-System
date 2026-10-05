"""SAP connector (light OData/RFC) — works with simulated data in local development."""
from __future__ import annotations

from typing import Any

from .base import BaseConnector, RawRecord
from .synthetic import connection_status, load_synthetic_oltp


class SAPConnector(BaseConnector):
    source_system = "SAP"

    def test_connection(self) -> dict[str, Any]:
        if self.connection_uri.startswith("simulated://") or self.connection_uri.startswith("sap://"):
            return connection_status(True, "sap odata/rfc adapter ready", "simulated")
        return connection_status(False, "SAP live endpoint not configured", "fallback")

    def extract(self, limit: int = 500) -> list[RawRecord]:
        # In a real environment: call an OData entity set or BAPI
        return load_synthetic_oltp(limit)
