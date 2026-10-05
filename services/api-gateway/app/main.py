"""API Gateway / Command Center — single entry point to the value chain microservices (R-GEN-02)."""
from __future__ import annotations

import logging

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from shared.audit import audit, list_audit
from shared.crypto import decrypt_sensitive, encrypt_sensitive, security_profile
from shared.i18n import t
from shared.logging_config import configure_logging
from shared.rate_limit import rate_limit_dependency
from shared.security_headers import SecurityHeadersMiddleware
from shared.settings import get_settings

from .auth import (
    create_access_token,
    create_pending_otp_token,
    decode_token,
    get_current_user,
    get_user_by_employee_code,
    require_role,
    verify_otp_code,
    verify_password,
)

settings = get_settings()
configure_logging("api-gateway", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - Command Center API Gateway",
    description="Integrated management panel for monitoring the entire value chain",
    version="5.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

_INTERNAL_SERVICES = {
    "data-integration": f"http://data-integration:{settings.data_integration_port}",
    "supply-chain-analytics": f"http://supply-chain-analytics:{settings.supply_chain_analytics_port}",
    "logistics": f"http://logistics:{settings.logistics_port}",
    "order-to-cash": f"http://order-to-cash:{settings.order_to_cash_port}",
    "bi-reporting": f"http://bi-reporting:{settings.bi_reporting_port}",
}


class LoginRequest(BaseModel):
    employee_code: str
    password: str


class OtpVerifyRequest(BaseModel):
    pending_token: str
    otp_code: str


class EncryptRequest(BaseModel):
    plaintext: str
    aad: str = "sensitive"


class DecryptRequest(BaseModel):
    token: str
    aad: str = "sensitive"


async def _proxy(service: str, method: str, path: str, **kwargs):
    base = _INTERNAL_SERVICES[service]
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.request(method, f"{base}{path}", **kwargs)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        if response.headers.get("content-type", "").startswith("application/json"):
            return response.json()
        return {"raw": response.text}


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "api-gateway",
        "phase": 5,
        "title": t("command_center_title", settings.default_locale),
        "availability_target": settings.target_availability,
    }


@app.get("/bench/ping")
async def bench_ping() -> dict:
    """Lightweight path for measuring horizontal capacity (NFR-SCL-01)."""
    return {"pong": True, "target_tps": settings.target_tps}


@app.get("/health/ha")
async def health_ha() -> dict:
    """Failover / HA status for the critical path."""
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=2.0) as client:
        for name, base_url in _INTERNAL_SERVICES.items():
            try:
                response = await client.get(f"{base_url}/health")
                results[name] = "up" if response.status_code == 200 else "degraded"
            except httpx.HTTPError:
                results[name] = "down"
    up = sum(1 for v in results.values() if v == "up")
    total = max(len(results), 1)
    return {
        "services": results,
        "up_ratio": round(up / total, 3),
        "ha_ready": up == total,
        "target_availability": settings.target_availability,
        "target_tps": settings.target_tps,
        "tls_min_version": settings.tls_min_version,
    }


@app.get("/health/services")
async def health_services() -> dict:
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, base_url in _INTERNAL_SERVICES.items():
            try:
                response = await client.get(f"{base_url}/health")
                results[name] = "up" if response.status_code == 200 else "degraded"
            except httpx.HTTPError:
                results[name] = "down"
    return results


@app.post("/auth/login")
async def login(
    body: LoginRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
) -> dict:
    user = get_user_by_employee_code(body.employee_code)
    client_ip = request.client.host if request.client else None
    if not user or not verify_password(body.password, user["password_hash"]):
        audit(
            action="auth.login",
            actor=body.employee_code,
            resource="api-gateway",
            outcome="failure",
            ip=client_ip,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect employee code or password.")

    if not user.get("two_factor_enabled") and not settings.two_factor_required:
        token = create_access_token(user["id"], user["employee_code"], user["role"])
        audit(
            action="auth.login",
            actor=user["employee_code"],
            resource="api-gateway",
            outcome="success",
            ip=client_ip,
            details={"requires_otp": False},
        )
        return {"requires_otp": False, "access_token": token, "token_type": "bearer"}

    pending_token = create_pending_otp_token(user["id"], user["employee_code"])
    audit(
        action="auth.login",
        actor=user["employee_code"],
        resource="api-gateway",
        outcome="success",
        ip=client_ip,
        details={"requires_otp": True},
    )
    return {"requires_otp": True, "pending_token": pending_token}


@app.post("/auth/verify-otp")
async def verify_otp(
    body: OtpVerifyRequest,
    request: Request,
    _: None = Depends(rate_limit_dependency),
) -> dict:
    payload = decode_token(body.pending_token)
    if payload.get("token_type") != "pending_otp":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The temporary token is invalid.")

    user = get_user_by_employee_code(payload["employee_code"])
    client_ip = request.client.host if request.client else None
    if not user or not user.get("otp_secret"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Two-factor authentication is not enabled.")

    if not verify_otp_code(user["otp_secret"], body.otp_code):
        audit(
            action="auth.verify_otp",
            actor=payload.get("employee_code", "unknown"),
            resource="api-gateway",
            outcome="failure",
            ip=client_ip,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="The one-time code is incorrect.")

    token = create_access_token(user["id"], user["employee_code"], user["role"])
    audit(
        action="auth.verify_otp",
        actor=user["employee_code"],
        resource="api-gateway",
        outcome="success",
        ip=client_ip,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "employee_code": user["employee_code"],
        "full_name": user.get("full_name"),
    }


@app.get("/security/profile")
async def get_security_profile(user: dict = Depends(require_role("admin", "executive"))) -> dict:
    return security_profile()


@app.get("/audit")
async def get_audit_log(
    limit: int = 100,
    user: dict = Depends(require_role("admin")),
) -> dict:
    return {"items": list_audit(limit=min(limit, 500)), "count": min(limit, 500)}


@app.post("/security/encrypt")
async def encrypt_payload(
    body: EncryptRequest,
    user: dict = Depends(require_role("admin", "executive")),
) -> dict:
    token = encrypt_sensitive(body.plaintext, aad=body.aad.encode("utf-8"))
    audit(
        action="security.encrypt",
        actor=user.get("employee_code", "unknown"),
        resource="sensitive_field",
        outcome="success",
        details={"aad": body.aad},
    )
    return {"algorithm": "AES-256-GCM", "token": token}


@app.post("/security/decrypt")
async def decrypt_payload(
    body: DecryptRequest,
    user: dict = Depends(require_role("admin")),
) -> dict:
    plaintext = decrypt_sensitive(body.token, aad=body.aad.encode("utf-8"))
    audit(
        action="security.decrypt",
        actor=user.get("employee_code", "unknown"),
        resource="sensitive_field",
        outcome="success",
        details={"aad": body.aad},
    )
    return {"plaintext": plaintext}


@app.get("/command-center/dashboard")
async def command_center_dashboard(
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
    locale: str = "fa",
    role: str = "analyst",
    user: dict = Depends(get_current_user),
) -> dict:
    params = {
        "subsidiary_code": subsidiary_code,
        "product_grade": product_grade,
        "region": region,
        "period": period,
        "locale": locale,
        "role": role,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return await _proxy("bi-reporting", "GET", "/dashboard", params=params)


@app.get("/reports/distribution")
async def distribution_report(
    subsidiary_code: str | None = None,
    region: str | None = None,
    period: str = "30d",
    locale: str = "fa",
    user: dict = Depends(require_role("analyst", "logistics", "executive", "admin")),
) -> dict:
    params = {
        "subsidiary_code": subsidiary_code,
        "region": region,
        "period": period,
        "locale": locale,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return await _proxy("bi-reporting", "GET", "/reports/distribution", params=params)


@app.get("/timeseries")
async def timeseries(
    metric: str = "operating_margin_percent",
    period: str = "30d",
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    user: dict = Depends(require_role("analyst", "executive", "admin")),
) -> dict:
    params = {
        "metric": metric,
        "period": period,
        "subsidiary_code": subsidiary_code,
        "product_grade": product_grade,
        "region": region,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return await _proxy("bi-reporting", "GET", "/timeseries", params=params)


@app.get("/alerts")
async def alerts(
    limit: int = 50,
    only_active: bool = False,
    locale: str = "fa",
    user: dict = Depends(get_current_user),
) -> dict:
    return await _proxy(
        "bi-reporting",
        "GET",
        "/alerts",
        params={"limit": limit, "only_active": only_active, "locale": locale},
    )


@app.post("/alerts/check-budgets")
async def check_budgets(user: dict = Depends(require_role("analyst", "executive", "admin"))) -> dict:
    return await _proxy("bi-reporting", "POST", "/alerts/check-budgets")


@app.post("/alerts/{alert_id}/acknowledge")
async def ack_alert(
    alert_id: int, payload: dict, user: dict = Depends(get_current_user)
) -> dict:
    return await _proxy("bi-reporting", "POST", f"/alerts/{alert_id}/acknowledge", json=payload)


@app.get("/i18n/{locale}")
async def i18n(locale: str, user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("bi-reporting", "GET", f"/i18n/{locale}")


@app.get("/filters")
async def filters(user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("bi-reporting", "GET", "/filters")


@app.get("/roles/{role}/views")
async def role_views(role: str, user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("bi-reporting", "GET", f"/roles/{role}/views")


@app.get("/auth/me")
async def auth_me(user: dict = Depends(get_current_user)) -> dict:
    return {
        "employee_code": user.get("employee_code"),
        "role": user.get("role"),
        "sub": user.get("sub"),
    }


@app.get("/patent/capabilities")
async def patent_capabilities(user: dict = Depends(get_current_user)) -> dict:
    """Summary of the patentable innovative capabilities implemented in the infrastructure."""
    return {
        "product": "Digital Transformation and Value Chain Integration",
        "differentiators_vs_honeywell": [
            "Data Mesh with decentralized domain ownership per subsidiary",
            "OLTP connectors (Oracle/SQLServer/PostgreSQL/SAP) + HS/UOM normalize pipeline",
            "Kafka domain topics + TimescaleDB time-series + data lineage",
            "Prophet/LSTM demand forecast + closed-loop feedstock LP maximizing holding margin",
            "Trading what-if scenarios + MLflow registry + drift monitoring",
            "Iran ports/customs/AIS+GPS live tracking with weather-aware ETA",
            "Order-to-Cash smart allocation + SAP-FI payment + customer portal",
            "Command Center BI with role-based multilingual dashboards",
            "Integrated cost-per-ton and unit-margin profitability reporting",
            "AES-256-GCM at-rest encryption + TLS 1.3 + audit log + rate limiting",
            "HA gateway pool (nginx) targeting 99.95% availability / 50k TPS scale path",
        ],
        "phases": {
            "1": "data-mesh-integration",
            "2": "supply-chain-intelligence",
            "3": "logistics-and-order-to-cash",
            "4": "command-center-and-executive-bi",
            "5": "scale-security-patent-readiness",
        },
        "modules": {
            "data-integration": "FR-DATA-01/02/03",
            "supply-chain-analytics": "FR-ML-01/02/03",
            "logistics": "FR-LOG-01/02/03",
            "order-to-cash": "FR-ORDER-01/02/03",
            "bi-reporting": "FR-BI-01/02/03",
            "command-center": "R-GEN-02 / R-GEN-04",
            "security-ha": "NFR-SEC-01/02 / NFR-AVAIL-01 / NFR-SCL-01",
        },
        "security": security_profile(),
    }


@app.get("/domains")
async def domains(user: dict = Depends(require_role("analyst", "supervisor", "executive", "admin"))) -> list:
    return await _proxy("data-integration", "GET", "/domains")


@app.post("/optimize/integrated")
async def optimize_integrated(
    payload: dict, user: dict = Depends(require_role("analyst", "executive", "admin"))
) -> dict:
    return await _proxy("supply-chain-analytics", "POST", "/optimize/integrated", json=payload)


@app.get("/optimize/latest")
async def latest_optimization(user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("supply-chain-analytics", "GET", "/optimize/latest")


@app.post("/forecast/demand")
async def forecast_demand(payload: dict, user: dict = Depends(require_role("analyst", "executive", "admin"))) -> dict:
    return await _proxy("supply-chain-analytics", "POST", "/forecast/demand", json=payload)


@app.post("/optimize/trading")
async def optimize_trading(payload: dict, user: dict = Depends(require_role("analyst", "executive", "admin"))) -> dict:
    return await _proxy("supply-chain-analytics", "POST", "/optimize/trading", json=payload)


@app.post("/train")
async def train_models(payload: dict, user: dict = Depends(require_role("analyst", "admin"))) -> dict:
    return await _proxy("supply-chain-analytics", "POST", "/train", json=payload)


@app.get("/drift")
async def drift(user: dict = Depends(require_role("analyst", "admin"))) -> list:
    return await _proxy("supply-chain-analytics", "GET", "/drift")


@app.post("/ingest")
async def ingest(payload: dict, user: dict = Depends(require_role("analyst", "admin"))) -> dict:
    return await _proxy("data-integration", "POST", "/ingest", json=payload)


@app.post("/connectors/register")
async def register_connector(payload: dict, user: dict = Depends(require_role("admin"))) -> dict:
    return await _proxy("data-integration", "POST", "/connectors/register", json=payload)


@app.get("/lineage")
async def lineage(user: dict = Depends(require_role("analyst", "admin"))) -> list:
    return await _proxy("data-integration", "GET", "/lineage")


@app.post("/orders")
async def create_order(payload: dict, user: dict = Depends(require_role("sales", "supervisor", "admin"))) -> dict:
    return await _proxy("order-to-cash", "POST", "/orders", json=payload)


@app.get("/orders")
async def list_orders(
    limit: int = 50, user: dict = Depends(require_role("sales", "logistics", "supervisor", "analyst", "admin"))
) -> list:
    return await _proxy("order-to-cash", "GET", "/orders", params={"limit": limit})


@app.get("/orders/{order_number}")
async def get_order(
    order_number: str, user: dict = Depends(require_role("sales", "logistics", "supervisor", "analyst", "admin"))
) -> dict:
    return await _proxy("order-to-cash", "GET", f"/orders/{order_number}")


@app.post("/orders/{order_number}/invoice")
async def invoice_order(
    order_number: str, user: dict = Depends(require_role("sales", "supervisor", "admin"))
) -> dict:
    return await _proxy("order-to-cash", "POST", f"/orders/{order_number}/invoice")


@app.post("/orders/{order_number}/ship")
async def ship_order(
    order_number: str, user: dict = Depends(require_role("logistics", "supervisor", "admin"))
) -> dict:
    return await _proxy("order-to-cash", "POST", f"/orders/{order_number}/ship")


@app.post("/invoices/{invoice_number}/payments")
async def pay_invoice(
    invoice_number: str, payload: dict, user: dict = Depends(require_role("sales", "admin"))
) -> dict:
    return await _proxy("order-to-cash", "POST", f"/invoices/{invoice_number}/payments", json=payload)


@app.get("/inventory")
async def inventory(user: dict = Depends(require_role("sales", "logistics", "analyst", "admin"))) -> dict:
    return await _proxy("order-to-cash", "GET", "/inventory")


@app.post("/shipments")
async def create_shipment(
    payload: dict, user: dict = Depends(require_role("logistics", "supervisor", "admin"))
) -> dict:
    return await _proxy("logistics", "POST", "/shipments", json=payload)


@app.get("/shipments")
async def list_shipments(
    limit: int = 50, user: dict = Depends(require_role("logistics", "supervisor", "analyst", "admin"))
) -> list:
    return await _proxy("logistics", "GET", "/shipments", params={"limit": limit})


@app.post("/shipments/live-track")
async def live_track(
    payload: dict, user: dict = Depends(require_role("logistics", "supervisor", "admin"))
) -> dict:
    return await _proxy("logistics", "POST", "/shipments/live-track", json=payload)


@app.get("/shipments/{shipment_number}")
async def get_shipment(shipment_number: str, user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("logistics", "GET", f"/shipments/{shipment_number}")


@app.get("/ports/iran")
async def iran_ports(user: dict = Depends(get_current_user)) -> dict:
    return await _proxy("logistics", "GET", "/ports/iran")


@app.get("/customer/orders/{order_number}/status")
async def customer_tracking(order_number: str, locale: str = "fa") -> dict:
    """Customer portal — without needing an internal login (self-service)."""
    return await _proxy("logistics", "GET", f"/customer/orders/{order_number}/status", params={"locale": locale})


@app.get("/customer/orders/{order_number}/portal")
async def customer_portal(order_number: str, locale: str = "fa") -> dict:
    return await _proxy(
        "order-to-cash", "GET", f"/customer/orders/{order_number}/portal", params={"locale": locale}
    )


@app.get("/reports/cost-per-ton")
async def cost_per_ton(
    subsidiary_code: str | None = None,
    product_grade: str | None = None,
    region: str | None = None,
    period: str = "30d",
    locale: str = "fa",
    user: dict = Depends(require_role("analyst", "executive", "admin")),
) -> dict:
    params = {
        "subsidiary_code": subsidiary_code,
        "product_grade": product_grade,
        "region": region,
        "period": period,
        "locale": locale,
    }
    params = {k: v for k, v in params.items() if v is not None}
    return await _proxy("bi-reporting", "GET", "/reports/cost-per-ton", params=params)
