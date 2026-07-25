"""Order-to-Cash Phase 3 — موجودی واقعی، تخصیص هوشمند، فاکتور/پرداخت، fulfillment لجستیک."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

import psycopg2
import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.logging_config import configure_logging
from shared.settings import get_settings

from .allocation import allocate
from .finance import get_invoice, invoices_for_order, issue_invoice, payments_for_invoice, record_payment
from .fulfillment import create_shipment_for_order
from .inventory import list_inventory, reserve, restock

settings = get_settings()
configure_logging("order-to-cash", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - Order-to-Cash Phase 3",
    description="Smart allocation + finance/ERP payments + logistics fulfillment",
    version="3.0.0",
)

_redis: redis.Redis | None = None
_ORDERS: dict[str, dict] = {}


def _pg_dsn() -> str:
    return settings.postgres_dsn.replace("postgresql+psycopg2", "postgresql")


def get_redis() -> redis.Redis | None:
    global _redis
    try:
        if _redis is None:
            _redis = redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=0.4)
            _redis.ping()
        return _redis
    except Exception:  # noqa: BLE001
        _redis = None
        return None


def _persist_order(order: dict) -> None:
    r = get_redis()
    if r is None:
        return
    try:
        r.set(f"dvc:order:{order['order_number']}", json.dumps(order))
    except Exception:  # noqa: BLE001
        pass


class CreateOrderRequest(BaseModel):
    channel: str = Field(pattern="^(online|contract|auction)$")
    product_grade: str
    quantity_tons: float = Field(gt=0)
    value_usd: float = Field(gt=0)
    customer_name: str = "Customer"
    customer_country: str = "AE"
    customer_lat: float = 25.2048
    customer_lon: float = 55.2708
    destination: str = "Jebel Ali"
    subsidiary_code: str = "NPC"
    prefer_port: bool = True
    auto_invoice: bool = False
    auto_ship: bool = False


class PaymentRequest(BaseModel):
    amount_usd: float = Field(gt=0)
    method: str = "wire"
    reference: str | None = None


class RestockRequest(BaseModel):
    warehouse_code: str
    product_grade: str
    quantity_tons: float = Field(gt=0)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "order-to-cash", "phase": 3}


@app.get("/inventory")
async def inventory() -> dict:
    rows = list_inventory()
    return {"warehouses": rows, "total_tons": round(sum(w["total_tons"] for w in rows), 2)}


@app.post("/inventory/restock")
async def inventory_restock(body: RestockRequest) -> dict:
    try:
        left = restock(body.warehouse_code, body.product_grade, body.quantity_tons)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"warehouse_code": body.warehouse_code, "product_grade": body.product_grade, "on_hand": left}


@app.post("/orders")
async def create_order(body: CreateOrderRequest) -> dict:
    try:
        allocation = allocate(
            quantity_tons=body.quantity_tons,
            product_grade=body.product_grade,
            customer_lat=body.customer_lat,
            customer_lon=body.customer_lon,
            prefer_port=body.prefer_port,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    selected = allocation["selected"]
    try:
        reserve(selected["code"], body.product_grade, body.quantity_tons)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    order_number = f"ORD-{uuid.uuid4().hex[:10].upper()}"
    order = {
        "order_number": order_number,
        "channel": body.channel,
        "product_grade": body.product_grade.upper(),
        "quantity_tons": body.quantity_tons,
        "value_usd": body.value_usd,
        "customer_name": body.customer_name,
        "customer_country": body.customer_country,
        "customer_lat": body.customer_lat,
        "customer_lon": body.customer_lon,
        "destination": body.destination,
        "subsidiary_code": body.subsidiary_code,
        "status": "allocated",
        "allocated_warehouse": selected["code"],
        "warehouse_city": selected["city"],
        "warehouse_port_code": selected.get("port_code"),
        "allocation_score": selected["score"],
        "distance_km": selected["distance_km"],
        "logistics_cost_usd": selected["logistics_cost_usd"],
        "inventory_remaining_at_wh": selected["inventory"] - body.quantity_tons,
        "allocation_alternatives": [
            {"code": a["code"], "score": a["score"], "inventory": a["inventory"]} for a in allocation["alternatives"]
        ],
        "invoice_number": None,
        "payment_status": "unpaid",
        "shipment_number": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _ORDERS[order_number] = order

    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orders
                    (order_number, channel, quantity_tons, value_usd, customer_name,
                     customer_country, status, subsidiary_id)
                VALUES (
                    %s, %s, %s, %s, %s, %s, 'allocated',
                    (SELECT id FROM subsidiaries WHERE code = %s LIMIT 1)
                )
                ON CONFLICT (order_number) DO NOTHING
                """,
                (
                    order_number,
                    body.channel,
                    body.quantity_tons,
                    body.value_usd,
                    body.customer_name,
                    body.customer_country,
                    body.subsidiary_code,
                ),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("order DB persist skipped: %s", exc)

    if body.auto_invoice:
        inv = issue_invoice(
            order_number=order_number,
            amount_usd=body.value_usd,
            customer_name=body.customer_name,
        )
        order["invoice_number"] = inv["invoice_number"]
        order["status"] = "invoiced"
        order["payment_status"] = inv["payment_status"]

    if body.auto_ship:
        shipment = await create_shipment_for_order(order)
        order["shipment_number"] = shipment.get("shipment_number")
        order["status"] = "shipped" if not shipment.get("offline") else "allocated"
        order["shipment"] = shipment

    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    _ORDERS[order_number] = order
    _persist_order(order)
    return order


@app.post("/orders/{order_number}/invoice")
async def create_invoice(order_number: str) -> dict:
    order = _ORDERS.get(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    inv = issue_invoice(
        order_number=order_number,
        amount_usd=order["value_usd"],
        customer_name=order["customer_name"],
    )
    order["invoice_number"] = inv["invoice_number"]
    order["status"] = "invoiced"
    order["payment_status"] = "unpaid"
    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    _ORDERS[order_number] = order
    _persist_order(order)

    try:
        with psycopg2.connect(_pg_dsn()) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO invoices (order_id, invoice_number, amount_usd, status)
                SELECT id, %s, %s, 'issued' FROM orders WHERE order_number = %s
                ON CONFLICT (invoice_number) DO NOTHING
                """,
                (inv["invoice_number"], order["value_usd"], order_number),
            )
            cur.execute(
                "UPDATE orders SET status='invoiced', updated_at=now() WHERE order_number=%s",
                (order_number,),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("invoice DB persist skipped: %s", exc)
    return inv


@app.post("/invoices/{invoice_number}/payments")
async def pay_invoice(invoice_number: str, body: PaymentRequest) -> dict:
    try:
        result = record_payment(
            invoice_number=invoice_number,
            amount_usd=body.amount_usd,
            method=body.method,
            reference=body.reference,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="invoice not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    order_number = result["invoice"]["order_number"]
    if order_number in _ORDERS:
        _ORDERS[order_number]["payment_status"] = result["invoice"]["payment_status"]
        if result["invoice"]["payment_status"] == "paid":
            _ORDERS[order_number]["status"] = "paid"
        _ORDERS[order_number]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _persist_order(_ORDERS[order_number])
    return result


@app.post("/orders/{order_number}/ship")
async def ship_order(order_number: str) -> dict:
    order = _ORDERS.get(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    shipment = await create_shipment_for_order(order)
    order["shipment_number"] = shipment.get("shipment_number")
    order["status"] = "shipped"
    order["shipment"] = shipment
    order["updated_at"] = datetime.now(timezone.utc).isoformat()
    _ORDERS[order_number] = order
    _persist_order(order)
    return {"order": order, "shipment": shipment}


@app.get("/orders/{order_number}")
async def get_order(order_number: str) -> dict:
    if order_number not in _ORDERS:
        raise HTTPException(status_code=404, detail="order not found")
    order = dict(_ORDERS[order_number])
    order["invoices"] = invoices_for_order(order_number)
    return order


@app.get("/orders")
async def list_orders(limit: int = 50) -> list[dict]:
    return list(_ORDERS.values())[-limit:]


@app.get("/invoices/{invoice_number}")
async def invoice_detail(invoice_number: str) -> dict:
    inv = get_invoice(invoice_number)
    if not inv:
        raise HTTPException(status_code=404, detail="invoice not found")
    return {**inv, "payments": payments_for_invoice(invoice_number)}


@app.get("/customer/orders/{order_number}/portal")
async def customer_portal(order_number: str, locale: str = "fa") -> dict:
    """پورتال مشتری: سفارش + فاکتور/پرداخت + لینک وضعیت محموله."""
    order = _ORDERS.get(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    invoices = invoices_for_order(order_number)
    messages = {
        "fa": f"سفارش {order_number} در وضعیت {order['status']}",
        "en": f"Order {order_number} is {order['status']}",
        "ar": f"الطلب {order_number} بحالة {order['status']}",
    }
    return {
        "order_number": order_number,
        "status": order["status"],
        "product_grade": order["product_grade"],
        "quantity_tons": order["quantity_tons"],
        "value_usd": order["value_usd"],
        "payment_status": order.get("payment_status"),
        "allocated_warehouse": order.get("allocated_warehouse"),
        "shipment_number": order.get("shipment_number"),
        "destination": order.get("destination"),
        "invoices": invoices,
        "tracking_url": f"/customer/orders/{order_number}/status",
        "message": messages.get(locale, messages["en"]),
        "portal": "order-to-cash-customer",
        "updated_at": order.get("updated_at"),
    }
