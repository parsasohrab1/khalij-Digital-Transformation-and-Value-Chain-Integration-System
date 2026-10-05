"""Logistics Phase 3 — AIS/GPS live, weather ETA, Iran customs, customer portal."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

import redis
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.db import dumps, pg_execute, pg_fetchall, pg_fetchone
from shared.logging_config import configure_logging
from shared.settings import get_settings

from .ais_gps import get_trail, get_vessel, register_vessel, simulate_live_track
from .customs import advance_clearance, by_shipment, create_declaration, get_declaration
from .eta import compute_eta
from .ports import IRAN_PORTS, get_port_live, list_ports_live, refresh_port_traffic
from .weather import estimate_weather, region_for_route

settings = get_settings()
configure_logging("logistics", settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khalij DVC - Logistics Phase 3",
    description="Live AIS/GPS + weather ETA + Iran customs + customer portal",
    version="3.1.0",
)

_redis: redis.Redis | None = None
_SHIPMENTS: dict[str, dict] = {}
_SHIPMENTS_HYDRATED = False
DESTINATIONS = {
    "Jebel Ali": {"lat": 25.0657, "lon": 55.1713},
    "Fujairah": {"lat": 25.1288, "lon": 56.3265},
    "Mumbai": {"lat": 18.9480, "lon": 72.8440},
    "Shanghai": {"lat": 31.2304, "lon": 121.4737},
}


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


def _save_shipment_db(shipment: dict) -> None:
    pg_execute(
        """
        INSERT INTO shipments (
            shipment_number, mode, origin_port, destination, customs_declaration,
            ais_mmsi, gps_device_id, eta_days, status, order_number, product_grade,
            quantity_tons, value_usd, payload_json, order_id, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb,
            (SELECT id FROM orders WHERE order_number = %s LIMIT 1), now()
        )
        ON CONFLICT (shipment_number) DO UPDATE SET
            status = EXCLUDED.status,
            eta_days = EXCLUDED.eta_days,
            customs_declaration = EXCLUDED.customs_declaration,
            order_number = EXCLUDED.order_number,
            payload_json = EXCLUDED.payload_json,
            updated_at = now()
        """,
        (
            shipment["shipment_number"],
            shipment.get("mode", "sea"),
            shipment.get("origin_port"),
            shipment.get("destination"),
            shipment.get("customs_declaration"),
            shipment.get("ais_mmsi"),
            shipment.get("gps_device_id"),
            shipment.get("eta_days"),
            shipment.get("status", "planned"),
            shipment.get("order_number"),
            shipment.get("product_grade"),
            shipment.get("quantity_tons"),
            shipment.get("value_usd"),
            dumps(shipment),
            shipment.get("order_number"),
        ),
    )


def _persist(shipment: dict) -> None:
    _SHIPMENTS[shipment["shipment_number"]] = shipment
    _save_shipment_db(shipment)
    r = get_redis()
    if r is None:
        return
    try:
        r.set(f"dvc:shipment:{shipment['shipment_number']}", json.dumps(shipment, default=str))
        if shipment.get("order_number"):
            r.set(f"dvc:order_shipment:{shipment['order_number']}", shipment["shipment_number"])
    except Exception:  # noqa: BLE001
        pass


def _load_shipment(shipment_number: str) -> dict | None:
    if shipment_number in _SHIPMENTS:
        return _SHIPMENTS[shipment_number]
    r = get_redis()
    if r:
        try:
            raw = r.get(f"dvc:shipment:{shipment_number}")
            if raw:
                s = json.loads(raw)
                _SHIPMENTS[shipment_number] = s
                return s
        except Exception:  # noqa: BLE001
            pass
    row = pg_fetchone("SELECT payload_json FROM shipments WHERE shipment_number=%s", (shipment_number,))
    if row and row.get("payload_json"):
        payload = row["payload_json"]
        if isinstance(payload, str):
            payload = json.loads(payload)
        _SHIPMENTS[shipment_number] = payload
        return payload
    return None


def _hydrate_shipments() -> None:
    global _SHIPMENTS_HYDRATED
    if _SHIPMENTS_HYDRATED:
        return
    for row in pg_fetchall(
        "SELECT shipment_number, payload_json FROM shipments WHERE payload_json IS NOT NULL ORDER BY id DESC LIMIT 500"
    ):
        payload = row.get("payload_json")
        if isinstance(payload, str):
            payload = json.loads(payload)
        if payload and payload.get("shipment_number"):
            _SHIPMENTS[payload["shipment_number"]] = payload
    _SHIPMENTS_HYDRATED = True


class CreateShipmentRequest(BaseModel):
    shipment_number: str | None = None
    order_number: str | None = None
    mode: str = Field(default="sea", pattern="^(sea|road|rail)$")
    origin_port: str = "BandarAbbas"
    destination: str = "Jebel Ali"
    destination_lat: float | None = None
    destination_lon: float | None = None
    product_grade: str = "HDPE"
    quantity_tons: float = 100.0
    value_usd: float = 100000.0
    ais_mmsi: str | None = None
    gps_device_id: str | None = None
    auto_customs: bool = True


class LiveTrackRequest(BaseModel):
    shipment_number: str
    progress: float = Field(default=0.35, ge=0, le=1)


class ETARequest(BaseModel):
    shipment_number: str
    weather_delay_hours: float | None = None
    destination_lat: float | None = None
    destination_lon: float | None = None


class CustomsAdvanceRequest(BaseModel):
    to_status: str | None = None


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": "logistics",
        "phase": 3,
        "patent": "iran-ports-customs-ais-gps",
    }


@app.get("/ports/iran")
async def list_iran_ports(live: bool = True) -> dict:
    ports = list_ports_live() if live else [
        {"port_key": k, **v} for k, v in IRAN_PORTS.items()
    ]
    return {"ports": ports, "integration": ["customs.gov.ir", "pmo.ir", "AIS", "GPS"]}


@app.post("/ports/{port_key}/refresh")
async def refresh_port(port_key: str) -> dict:
    if port_key not in IRAN_PORTS:
        raise HTTPException(status_code=404, detail="unknown port")
    return refresh_port_traffic(port_key)


@app.get("/weather")
async def weather(origin_port: str = "BandarAbbas", destination: str = "Jebel Ali") -> dict:
    region = region_for_route(origin_port, destination)
    return estimate_weather(region)


@app.post("/shipments")
async def create_shipment(body: CreateShipmentRequest) -> dict:
    if body.origin_port not in IRAN_PORTS:
        raise HTTPException(status_code=400, detail=f"invalid origin_port: {list(IRAN_PORTS)}")

    port = get_port_live(body.origin_port)
    dest = DESTINATIONS.get(body.destination, {"lat": 25.0657, "lon": 55.1713})
    dest_lat = body.destination_lat if body.destination_lat is not None else dest["lat"]
    dest_lon = body.destination_lon if body.destination_lon is not None else dest["lon"]
    shipment_number = body.shipment_number or f"SHP-{uuid.uuid4().hex[:10].upper()}"
    mmsi = body.ais_mmsi or f"422{uuid.uuid4().int % 10**6:06d}"
    register_vessel(mmsi, f"KF-{shipment_number}", "cargo")

    shipment = {
        "shipment_number": shipment_number,
        "order_number": body.order_number,
        "mode": body.mode,
        "origin_port": body.origin_port,
        "origin_port_code": port["code"],
        "pmo_code": port["pmo_code"],
        "customs_office": port["customs_office"],
        "destination": body.destination,
        "destination_lat": dest_lat,
        "destination_lon": dest_lon,
        "product_grade": body.product_grade,
        "quantity_tons": body.quantity_tons,
        "value_usd": body.value_usd,
        "ais_mmsi": mmsi,
        "gps_device_id": body.gps_device_id or f"GPS-{shipment_number}",
        "status": "planned",
        "latitude": port["lat"],
        "longitude": port["lon"],
        "speed_knots": 0.0,
        "eta_days": None,
        "customs_declaration": None,
        "customs_status": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    if body.auto_customs:
        decl = create_declaration(
            shipment_number=shipment_number,
            origin_port_code=port["code"],
            customs_office=port["customs_office"],
            product_grade=body.product_grade,
            quantity_tons=body.quantity_tons,
            value_usd=body.value_usd,
        )
        shipment["customs_declaration"] = decl["declaration_number"]
        shipment["customs_status"] = decl["status"]
        shipment["hs_code"] = decl["hs_code"]
        shipment["epl_ref"] = decl["epl_ref"]

    _SHIPMENTS[shipment_number] = shipment
    _persist(shipment)
    return shipment


@app.post("/shipments/live-track")
async def live_track(body: LiveTrackRequest) -> dict:
    shipment = _load_shipment(body.shipment_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="shipment not found")

    track = simulate_live_track(
        body.shipment_number,
        IRAN_PORTS[shipment["origin_port"]]["lat"],
        IRAN_PORTS[shipment["origin_port"]]["lon"],
        shipment["destination_lat"],
        shipment["destination_lon"],
        progress=body.progress,
        mmsi=shipment.get("ais_mmsi"),
    )
    shipment.update(
        {
            "latitude": track["latitude"],
            "longitude": track["longitude"],
            "speed_knots": track["speed_knots"],
            "heading_deg": track["heading_deg"],
            "position_source": track["fused_source"],
            "progress": body.progress,
            "status": "in_transit" if body.progress < 0.95 else "arrived",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    eta = compute_eta(
        origin_port=shipment["origin_port"],
        latitude=shipment["latitude"],
        longitude=shipment["longitude"],
        speed_knots=shipment["speed_knots"],
        destination=shipment["destination"],
        destination_lat=shipment["destination_lat"],
        destination_lon=shipment["destination_lon"],
    )
    shipment["eta_days"] = eta["eta_days"]
    shipment["eta_breakdown"] = eta["breakdown"]
    shipment["weather"] = eta["weather"]
    _SHIPMENTS[body.shipment_number] = shipment
    _persist(shipment)
    return {"shipment": shipment, "track": track, "eta": eta}


@app.post("/shipments/eta")
async def calculate_eta(body: ETARequest) -> dict:
    shipment = _load_shipment(body.shipment_number)
    if not shipment:
        raise HTTPException(status_code=404, detail="shipment not found")
    eta = compute_eta(
        origin_port=shipment["origin_port"],
        latitude=shipment.get("latitude", IRAN_PORTS[shipment["origin_port"]]["lat"]),
        longitude=shipment.get("longitude", IRAN_PORTS[shipment["origin_port"]]["lon"]),
        speed_knots=float(shipment.get("speed_knots") or 12.0),
        destination=shipment["destination"],
        destination_lat=body.destination_lat or shipment["destination_lat"],
        destination_lon=body.destination_lon or shipment["destination_lon"],
        weather_override_hours=body.weather_delay_hours,
    )
    shipment["eta_days"] = eta["eta_days"]
    shipment["eta_breakdown"] = eta["breakdown"]
    shipment["weather"] = eta["weather"]
    shipment["updated_at"] = datetime.now(timezone.utc).isoformat()
    _SHIPMENTS[body.shipment_number] = shipment
    _persist(shipment)
    return shipment


@app.get("/shipments/{shipment_number}")
async def get_shipment(shipment_number: str) -> dict:
    shipment = _load_shipment(shipment_number)
    if shipment:
        return shipment
    raise HTTPException(status_code=404, detail="shipment not found")


@app.get("/shipments/{shipment_number}/trail")
async def shipment_trail(shipment_number: str, limit: int = 50) -> dict:
    return {"shipment_number": shipment_number, "trail": get_trail(shipment_number, limit)}


@app.get("/ais/{mmsi}")
async def ais_vessel(mmsi: str) -> dict:
    vessel = get_vessel(mmsi)
    if not vessel:
        raise HTTPException(status_code=404, detail="vessel not found")
    return vessel


@app.post("/customs/{declaration_number}/advance")
async def customs_advance(declaration_number: str, body: CustomsAdvanceRequest | None = None) -> dict:
    try:
        decl = advance_clearance(declaration_number, body.to_status if body else None)
    except KeyError:
        raise HTTPException(status_code=404, detail="declaration not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for s in _SHIPMENTS.values():
        if s.get("customs_declaration") == declaration_number:
            s["customs_status"] = decl["status"]
            if decl["cleared"] and s["status"] == "planned":
                s["status"] = "cleared_for_export"
            _persist(s)
    return decl


@app.get("/customs/{declaration_number}")
async def customs_get(declaration_number: str) -> dict:
    decl = get_declaration(declaration_number)
    if not decl:
        raise HTTPException(status_code=404, detail="declaration not found")
    return decl


@app.get("/customer/orders/{order_number}/status")
async def customer_order_status(order_number: str, locale: str = "fa") -> dict:
    """Customer portal — order + shipment + ETA + customs (FR-LOG-03)."""
    _hydrate_shipments()
    matched = [s for s in _SHIPMENTS.values() if s.get("order_number") == order_number]
    if not matched:
        r = get_redis()
        if r:
            try:
                sh_no = r.get(f"dvc:order_shipment:{order_number}")
                if sh_no:
                    s = _load_shipment(sh_no)
                    if s:
                        matched = [s]
            except Exception:  # noqa: BLE001
                pass
    if not matched:
        rows = pg_fetchall(
            "SELECT payload_json FROM shipments WHERE order_number=%s ORDER BY id DESC LIMIT 1",
            (order_number,),
        )
        for row in rows:
            payload = row.get("payload_json")
            if isinstance(payload, str):
                payload = json.loads(payload)
            if payload:
                matched = [payload]
                _SHIPMENTS[payload["shipment_number"]] = payload
    if not matched:
        msg = {
            "fa": "No order with this number was found or it has not been shipped yet",
            "en": "Order not found or not yet shipped",
            "ar": "لم يتم العثور على الطلب أو لم يتم شحنه بعد",
        }
        return {"order_number": order_number, "status": "unknown", "message": msg.get(locale, msg["en"])}

    s = matched[0]
    customs = by_shipment(s["shipment_number"])
    msg = {
        "fa": f"Shipment status: {s['status']} — ETA about {s.get('eta_days')} days",
        "en": f"Shipment status: {s['status']} — ETA ~{s.get('eta_days')} days",
        "ar": f"حالة الشحنة: {s['status']} — الوصول خلال {s.get('eta_days')} أيام تقريباً",
    }
    return {
        "order_number": order_number,
        "shipment_number": s["shipment_number"],
        "status": s["status"],
        "origin_port": s["origin_port"],
        "origin_port_code": s.get("origin_port_code"),
        "pmo_code": s.get("pmo_code"),
        "destination": s["destination"],
        "eta_days": s.get("eta_days"),
        "eta_breakdown": s.get("eta_breakdown"),
        "weather": s.get("weather"),
        "last_position": {
            "lat": s.get("latitude"),
            "lon": s.get("longitude"),
            "source": s.get("position_source"),
            "speed_knots": s.get("speed_knots"),
        },
        "customs_declaration": s.get("customs_declaration"),
        "customs_status": s.get("customs_status"),
        "hs_code": s.get("hs_code"),
        "customs": customs[0] if customs else None,
        "message": msg.get(locale, msg["en"]),
        "portal": "customer-self-service",
        "updated_at": s.get("updated_at"),
    }


@app.get("/shipments")
async def list_shipments(limit: int = 50) -> list[dict]:
    _hydrate_shipments()
    return list(_SHIPMENTS.values())[-limit:]
