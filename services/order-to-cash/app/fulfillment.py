"""اتصال سفارش به محموله لجستیک (Well-to-Market fulfillment)."""
from __future__ import annotations

from typing import Any

import httpx

from shared.settings import get_settings

settings = get_settings()


async def create_shipment_for_order(order: dict[str, Any], origin_port: str | None = None) -> dict[str, Any]:
    """فراخوانی سرویس logistics برای ایجاد محموله و اظهارنامه گمرکی."""
    port = origin_port
    if not port:
        # map warehouse -> port
        wh = order.get("allocated_warehouse")
        port = {"WH-BND": "BandarAbbas", "WH-ASL": "Assaluyeh"}.get(wh, "BandarAbbas")

    payload = {
        "order_number": order["order_number"],
        "origin_port": port,
        "destination": order.get("destination", "Jebel Ali"),
        "product_grade": order["product_grade"],
        "quantity_tons": order["quantity_tons"],
        "value_usd": order["value_usd"],
        "auto_customs": True,
        "mode": "sea",
    }
    url = f"http://logistics:{settings.logistics_port}/shipments"
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code < 400:
                return resp.json()
    except Exception:  # noqa: BLE001
        pass

    # fallback محلی اگر logistics در دسترس نباشد
    return {
        "shipment_number": f"LOCAL-{order['order_number']}",
        "order_number": order["order_number"],
        "origin_port": port,
        "status": "planned",
        "offline": True,
    }
