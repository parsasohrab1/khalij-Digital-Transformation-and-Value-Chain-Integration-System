"""Data Integration Hub — فاز ۱: کانکتور واقعی، استانداردسازی، Kafka، Timescale، Lineage.

نوآوری ثبت اختراع: Data Mesh با مالکیت غیرمتمرکز داده به‌ازای هر شرکت تابعه.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.events import IngestBatchResult
from shared.logging_config import configure_logging
from shared.schemas import DomainOwnership
from shared.settings import get_settings

from .connectors.factory import create_connector
from .lineage_service import list_lineage, record_lineage
from .normalize import normalize_batch
from .publisher import DomainEventPublisher
from .timescale_loader import load_inventory_and_prices, memory_stats

settings = get_settings()
configure_logging("data-integration", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - Data Integration Hub (Phase 1)",
    description="Data Mesh: connectors + HS/UOM normalize + Kafka domain topics + Timescale + Lineage",
    version="2.0.0",
)

SUPPORTED_SOURCE_SYSTEMS = {"Oracle", "SQLServer", "PostgreSQL", "SAP", "ERP"}
publisher = DomainEventPublisher()
_CONNECTORS: dict[str, dict] = {}


def _pg_dsn() -> str:
    return settings.postgres_dsn.replace("postgresql+psycopg2", "postgresql")


class ConnectRequest(BaseModel):
    source_system: str = Field(description="Oracle | SQLServer | PostgreSQL | SAP | ERP")
    subsidiary_code: str
    connection_uri: str = Field(default="simulated://oltp")
    source_entity: str = Field(default="sales.orders")
    domain_owner: str | None = None


class IngestRequest(BaseModel):
    connector_key: str | None = None
    source_system: str = "PostgreSQL"
    subsidiary_code: str = "NPC"
    connection_uri: str = "simulated://oltp"
    source_entity: str = "sales.orders"
    limit: int = Field(default=200, ge=1, le=5000)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "data-integration",
        "architecture": "data-mesh",
        "phase": 1,
        "patent": "decentralized-domain-ownership",
    }


@app.get("/domains", response_model=list[DomainOwnership])
async def list_domains() -> list[DomainOwnership]:
    query = """
        SELECT code AS subsidiary_code, domain_owner, kafka_topic
        FROM subsidiaries WHERE is_active = TRUE ORDER BY code
    """
    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query)
            rows = cur.fetchall()
            return [
                DomainOwnership(
                    subsidiary_code=r["subsidiary_code"],
                    domain_owner=r["domain_owner"],
                    kafka_topic=r["kafka_topic"],
                    source_system="PostgreSQL",
                )
                for r in rows
            ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("domains offline fallback: %s", exc)
        return [
            DomainOwnership(
                subsidiary_code=code,
                domain_owner=f"{code.lower()}-data-owner",
                kafka_topic=f"{settings.kafka_topic_subsidiary_prefix}.{code.lower()}",
                source_system=src,
            )
            for code, src in [("NPC", "SAP"), ("BIPC", "Oracle"), ("PIDMCO", "SQLServer"), ("ARPC", "PostgreSQL")]
        ]


@app.post("/connectors/register")
async def register_connector(body: ConnectRequest) -> dict:
    if body.source_system not in SUPPORTED_SOURCE_SYSTEMS:
        raise HTTPException(status_code=400, detail=f"unsupported source: {body.source_system}")

    topic = publisher.subsidiary_topic(body.subsidiary_code)
    key = f"{body.subsidiary_code.lower()}-{body.source_system.lower()}"
    owner = body.domain_owner or f"{body.subsidiary_code.lower()}-data-owner"

    connector = create_connector(body.source_system, body.connection_uri, body.source_entity, body.subsidiary_code)
    status = connector.test_connection()

    meta = {
        "connector_key": key,
        "source_system": body.source_system,
        "subsidiary_code": body.subsidiary_code,
        "connection_uri": body.connection_uri,
        "source_entity": body.source_entity,
        "kafka_topic": topic,
        "domain_owner": owner,
        "connection_status": status,
    }
    _CONNECTORS[key] = meta

    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO data_connectors
                    (connector_key, source_system, subsidiary_code, connection_uri, source_entity, kafka_topic, domain_owner)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (connector_key) DO UPDATE SET
                    connection_uri = EXCLUDED.connection_uri,
                    source_entity = EXCLUDED.source_entity,
                    is_active = TRUE
                """,
                (key, body.source_system, body.subsidiary_code, body.connection_uri, body.source_entity, topic, owner),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("connector registry DB skipped: %s", exc)

    lineage_id = record_lineage(
        source_system=body.source_system,
        source_entity=body.source_entity,
        domain_code=body.subsidiary_code,
        target_topic=topic,
        target_table="orders",
        transform_note="register connector; HS+UOM normalize pipeline attached",
        records_count=0,
        extra={"domain_owner": owner, "mode": status.get("mode")},
    )
    return {"status": "registered", "connector": meta, "lineage_id": lineage_id, "patent_note": "data-mesh-ownership"}


@app.get("/connectors")
async def list_connectors() -> list[dict]:
    if _CONNECTORS:
        return list(_CONNECTORS.values())
    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM data_connectors WHERE is_active ORDER BY connector_key")
            return [dict(r) for r in cur.fetchall()]
    except Exception:  # noqa: BLE001
        return []


@app.post("/ingest", response_model=IngestBatchResult)
async def ingest_batch(body: IngestRequest) -> IngestBatchResult:
    """استخراج → نرمال‌سازی HS/UOM → Kafka (topic تابعه) → Timescale → Lineage."""
    meta = _CONNECTORS.get(body.connector_key) if body.connector_key else None
    source_system = meta["source_system"] if meta else body.source_system
    subsidiary = meta["subsidiary_code"] if meta else body.subsidiary_code
    uri = meta["connection_uri"] if meta else body.connection_uri
    entity = meta["source_entity"] if meta else body.source_entity
    key = body.connector_key or f"{subsidiary.lower()}-{source_system.lower()}"

    connector = create_connector(source_system, uri, entity, subsidiary)
    raw = connector.extract(limit=body.limit)
    normalized = normalize_batch(raw, subsidiary)
    topic = publisher.subsidiary_topic(subsidiary)

    events_published = 0
    for rec in normalized:
        events_published += publisher.publish(
            event_type="product.normalized",
            subsidiary_code=subsidiary,
            source=f"{source_system.lower()}://{subsidiary}/{entity}",
            data=rec.model_dump(),
            also_domain_topic=settings.kafka_topic_orders,
        )

    # رویداد موجودی/قیمت برای سری زمانی
    for r in raw[:50]:
        if r.warehouse_code:
            events_published += publisher.publish(
                event_type="inventory.snapshot",
                subsidiary_code=subsidiary,
                source=f"{source_system.lower()}://{subsidiary}/inventory",
                data={
                    "warehouse_code": r.warehouse_code,
                    "product_grade": r.grade,
                    "quantity_tons": r.quantity,
                    "timestamp": (r.timestamp or datetime.now(timezone.utc)).isoformat(),
                },
                also_domain_topic=settings.kafka_topic_inventory,
            )
        if r.oil_price is not None:
            events_published += publisher.publish(
                event_type="price.tick",
                subsidiary_code=subsidiary,
                source=f"{source_system.lower()}://{subsidiary}/prices",
                data={
                    "oil_price_usd_bbl": r.oil_price,
                    "price_hdpe_usd_ton": r.price_hdpe,
                    "price_pp_usd_ton": r.price_pp,
                    "feedstock_price_usd_ton": r.feedstock_price,
                    "timestamp": (r.timestamp or datetime.now(timezone.utc)).isoformat(),
                },
                also_domain_topic=settings.kafka_topic_prices,
            )

    ts_rows = load_inventory_and_prices(raw)
    lineage_id = record_lineage(
        source_system=source_system,
        source_entity=entity,
        domain_code=subsidiary,
        target_topic=topic,
        target_table="inventory_ts,market_prices_ts",
        transform_note="extract→HS/UOM normalize→kafka domain topic→timescale",
        records_count=len(normalized),
        extra={"connector_key": key, "timescale_rows": ts_rows},
    )

    return IngestBatchResult(
        connector_id=key,
        subsidiary_code=subsidiary,
        source_system=source_system,
        records_in=len(raw),
        records_normalized=len(normalized),
        events_published=events_published,
        kafka_topic=topic,
        lineage_id=lineage_id,
        timescale_rows=ts_rows,
    )


@app.get("/products/normalize")
async def normalize_product(
    internal_code: str | None = None, hs_code: str | None = None, grade: str | None = None
) -> dict:
    from .normalize import GRADE_TO_HS, GRADE_TO_INTERNAL

    if grade:
        g = grade.upper()
        return {
            "matches": [
                {
                    "internal_code": GRADE_TO_INTERNAL.get(g, internal_code),
                    "hs_code": GRADE_TO_HS.get(g, hs_code),
                    "grade": g,
                    "uom": "ton",
                }
            ],
            "canonical_uom": "ton",
        }
    if not any([internal_code, hs_code, grade]):
        raise HTTPException(status_code=400, detail="provide internal_code / hs_code / grade")
    return {"matches": [], "canonical_uom": "ton"}


@app.get("/lineage")
async def lineage(limit: int = 50) -> list[dict]:
    return list_lineage(limit)


@app.get("/events/offline")
async def offline_events(limit: int = 50) -> list[dict]:
    return publisher.offline_buffer(limit)


@app.get("/timescale/stats")
async def timescale_stats() -> dict:
    return {"memory_buffer": memory_stats()}
