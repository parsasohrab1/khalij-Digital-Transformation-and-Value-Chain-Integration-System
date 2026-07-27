"""Smoke tests for Demo MVP happy path (offline-friendly)."""
from __future__ import annotations

import sys
from pathlib import Path

import pyotp
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.ensure_seed_data import ensure_seed_data
from shared.crypto import decrypt_sensitive, encrypt_sensitive


def _load_app(service_dir: str):
    service_path = ROOT / "services" / service_dir
    for key in list(sys.modules):
        if key == "app" or key.startswith("app."):
            del sys.modules[key]
    if str(service_path) in sys.path:
        sys.path.remove(str(service_path))
    sys.path.insert(0, str(service_path))
    from app.main import app  # noqa: WPS433

    return app


@pytest.fixture(scope="module", autouse=True)
def _seed():
    ensure_seed_data()


def test_aes_roundtrip():
    token = encrypt_sensitive("price-1000", aad=b"demo")
    assert decrypt_sensitive(token, aad=b"demo") == "price-1000"


def test_bi_dashboard_from_csv():
    client = TestClient(_load_app("bi-reporting"))
    health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["data_source"]["source"] == "csv"
    dash = client.get("/dashboard", params={"role": "admin", "period": "30d", "locale": "fa"}).json()
    assert dash["kpis"]["data_source"] == "csv"
    assert "operating_margin_percent" in dash["kpis"]
    cost = client.get("/reports/cost-per-ton").json()
    assert cost["units"]
    assert cost["holding_avg_margin_percent"] > 0


def test_optimize_closed_loop():
    client = TestClient(_load_app("supply-chain-analytics"))
    r = client.post(
        "/optimize/integrated",
        json={
            "horizon_days": 30,
            "available_feedstock_tons": 2500,
            "oil_price_usd_bbl": 75,
            "model": "prophet",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["closed_loop"] is True
    assert body["holding_margin_usd"] is not None


def test_order_and_shipment():
    otc = TestClient(_load_app("order-to-cash"))
    order = otc.post(
        "/orders",
        json={
            "channel": "contract",
            "product_grade": "HDPE",
            "quantity_tons": 80,
            "value_usd": 90000,
            "auto_invoice": True,
            "destination": "Jebel Ali",
        },
    ).json()
    assert order["order_number"].startswith("ORD-")
    assert order["allocated_warehouse"]

    lg = TestClient(_load_app("logistics"))
    ship = lg.post(
        "/shipments",
        json={
            "order_number": order["order_number"],
            "origin_port": "Assaluyeh",
            "destination": "Jebel Ali",
            "product_grade": "HDPE",
            "quantity_tons": 80,
            "value_usd": 90000,
        },
    ).json()
    assert ship["shipment_number"].startswith("SHP-")
    track = lg.post(
        "/shipments/live-track",
        json={"shipment_number": ship["shipment_number"], "progress": 0.4},
    ).json()
    assert "shipment" in track


def test_gateway_auth_security_headers():
    client = TestClient(_load_app("api-gateway"))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers.get("x-content-type-options") == "nosniff"
    assert "TLSv1.3" in (health.headers.get("x-tls-min-version") or "")

    login = client.post("/auth/login", json={"employee_code": "demo-admin", "password": "ChangeMe123!"})
    assert login.status_code == 200
    pending = login.json()["pending_token"]
    otp = pyotp.TOTP("3MYXLVCKBIRJUTD6").now()
    verified = client.post("/auth/verify-otp", json={"pending_token": pending, "otp_code": otp})
    assert verified.status_code == 200
    token = verified.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "admin"

    enc = client.post(
        "/security/encrypt",
        headers=headers,
        json={"plaintext": "secret-contract", "aad": "price"},
    )
    assert enc.status_code == 200
    assert enc.json()["algorithm"] == "AES-256-GCM"

    profile = client.get("/security/profile", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["at_rest"] == "AES-256-GCM"
