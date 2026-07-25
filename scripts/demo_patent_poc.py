"""PoC دمو قابلیت‌های ثبت اختراع — مسیر یکپارچه Well-to-Market."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fastapi.testclient import TestClient

from shared.audit import audit
from shared.crypto import encrypt_sensitive, security_profile


def load_app(service_dir: str):
    """هر سرویس را با پاک‌سازی ماژول app قبلی لود می‌کند تا تداخل import نباشد."""
    service_path = ROOT / "services" / service_dir
    # remove previous service package modules
    for key in list(sys.modules):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]
    if str(service_path) in sys.path:
        sys.path.remove(str(service_path))
    sys.path.insert(0, str(service_path))
    from app.main import app  # noqa: WPS433

    return app


def section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def main() -> None:
    section("1) Data Mesh ingest (Phase 1)")
    di = TestClient(load_app("data-integration"))
    reg = di.post(
        "/connectors/register",
        json={
            "source_system": "Oracle",
            "subsidiary_code": "BIPC",
            "connection_uri": "simulated://oracle",
            "source_entity": "SALES.ORDERS",
        },
    ).json()
    ingest = di.post(
        "/ingest",
        json={
            "source_system": "Oracle",
            "subsidiary_code": "BIPC",
            "connection_uri": "simulated://oracle",
            "limit": 40,
        },
    ).json()
    print("connector=", reg.get("connector", {}).get("connector_key"), "topic=", ingest.get("kafka_topic"))
    print("normalized=", ingest.get("records_normalized"), "lineage=", ingest.get("lineage_id"))

    section("2) Integrated optimization (Phase 2)")
    sc = TestClient(load_app("supply-chain-analytics"))
    opt = sc.post(
        "/optimize/integrated",
        json={
            "horizon_days": 90,
            "available_feedstock_tons": 3500,
            "oil_price_usd_bbl": 78,
            "model": "ensemble",
            "what_if": {"oil_shock_pct": 5},
        },
    ).json()
    print(
        "margin=",
        opt.get("holding_margin_usd"),
        "model=",
        opt.get("model_name"),
        "closed_loop=",
        opt.get("closed_loop"),
        "ms=",
        opt.get("latency_ms"),
    )

    section("3) Iran logistics + customs (Phase 3)")
    lg = TestClient(load_app("logistics"))
    ship = lg.post(
        "/shipments",
        json={
            "order_number": "ORD-POC-1",
            "origin_port": "Assaluyeh",
            "destination": "Jebel Ali",
            "product_grade": "HDPE",
            "quantity_tons": 200,
            "value_usd": 220000,
        },
    ).json()
    track = lg.post(
        "/shipments/live-track",
        json={"shipment_number": ship["shipment_number"], "progress": 0.45},
    ).json()
    print(
        "shipment=",
        ship["shipment_number"],
        "customs=",
        ship.get("customs_declaration"),
        "eta=",
        track["shipment"].get("eta_days"),
    )

    section("4) Order-to-Cash + AES-256 price (Phase 3/5)")
    otc = TestClient(load_app("order-to-cash"))
    order = otc.post(
        "/orders",
        json={
            "channel": "contract",
            "product_grade": "HDPE",
            "quantity_tons": 150,
            "value_usd": 180000,
            "auto_invoice": True,
            "destination": "Jebel Ali",
        },
    ).json()
    enc_price = encrypt_sensitive(str(order["value_usd"]), aad=b"contract_price")
    print("order=", order["order_number"], "warehouse=", order["allocated_warehouse"])
    print("enc_price=", enc_price[:32] + "...")

    section("5) Command Center BI (Phase 4)")
    bi = TestClient(load_app("bi-reporting"))
    dash = bi.get("/dashboard", params={"role": "executive", "locale": "fa", "period": "30d"}).json()
    cost = bi.get("/reports/cost-per-ton").json()
    print("title=", dash["title"], "avg_margin%=", cost["holding_avg_margin_percent"])

    section("6) Security profile + audit (Phase 5)")
    audit(
        action="patent_poc_demo",
        actor="demo",
        resource="end-to-end",
        outcome="success",
        details={"order": order["order_number"], "shipment": ship["shipment_number"]},
    )
    print(json.dumps(security_profile(), ensure_ascii=False, indent=2))
    print("\n✅ Patent PoC demo finished successfully")


if __name__ == "__main__":
    main()
