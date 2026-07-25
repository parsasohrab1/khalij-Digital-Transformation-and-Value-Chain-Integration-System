"""کارخانه ساخت کانکتور بر اساس نوع سیستم منبع."""
from __future__ import annotations

from .base import BaseConnector
from .oracle_conn import OracleConnector
from .postgres_conn import PostgreSQLConnector
from .sap_conn import SAPConnector
from .sqlserver_conn import SQLServerConnector

_REGISTRY = {
    "PostgreSQL": PostgreSQLConnector,
    "Oracle": OracleConnector,
    "SQLServer": SQLServerConnector,
    "SAP": SAPConnector,
    "ERP": SAPConnector,
}


def create_connector(
    source_system: str, connection_uri: str, source_entity: str, subsidiary_code: str
) -> BaseConnector:
    cls = _REGISTRY.get(source_system)
    if cls is None:
        raise ValueError(f"unsupported source_system: {source_system}")
    return cls(connection_uri, source_entity, subsidiary_code)
