"""Base OLTP/ERP connector for the Data Mesh architecture."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class RawRecord:
    source_sku: str
    grade: str
    quantity: float
    uom: str
    hs_code: str | None = None
    warehouse_code: str | None = None
    oil_price: float | None = None
    price_hdpe: float | None = None
    price_pp: float | None = None
    feedstock_price: float | None = None
    timestamp: datetime | None = None
    extra: dict[str, Any] | None = None


class BaseConnector(ABC):
    source_system: str

    def __init__(self, connection_uri: str, source_entity: str, subsidiary_code: str):
        self.connection_uri = connection_uri
        self.source_entity = source_entity
        self.subsidiary_code = subsidiary_code

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        ...

    @abstractmethod
    def extract(self, limit: int = 500) -> list[RawRecord]:
        ...
