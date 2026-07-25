"""قرارداد رویدادهای Kafka برای Data Mesh (نسخه‌بندی‌شده).

هر شرکت تابعه topic اختصاصی دارد: dvc.subsidiary.{code}
رویدادهای دامنه روی topic مشترک نیز publish می‌شوند.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

SCHEMA_VERSION = "1.0.0"

EventType = Literal[
    "order.created",
    "inventory.snapshot",
    "price.tick",
    "product.normalized",
    "lineage.recorded",
]


class CloudEventEnvelope(BaseModel):
    """قرارداد یکنواخت رویداد — سازگار با الگوی CloudEvents سبک."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source: str  # e.g. oracle://bipc/sales.orders
    type: EventType
    subject: str  # subsidiary code
    time: datetime = Field(default_factory=datetime.utcnow)
    dataschema: str = f"khalij.dvc.events/{SCHEMA_VERSION}"
    data: dict[str, Any]


class NormalizedProductRecord(BaseModel):
    source_sku: str
    internal_code: str
    hs_code: str
    grade: str
    quantity_raw: float
    uom_raw: str
    quantity_tons: float
    uom_canonical: Literal["ton"] = "ton"
    subsidiary_code: str


class IngestBatchResult(BaseModel):
    connector_id: str
    subsidiary_code: str
    source_system: str
    records_in: int
    records_normalized: int
    events_published: int
    kafka_topic: str
    lineage_id: str | None = None
    timescale_rows: int = 0
