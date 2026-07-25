"""Iran customs declaration and clearance workflow (customs.gov.ir simulated)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

GRADE_TO_HS = {
    "HDPE": "390120",
    "LDPE": "390110",
    "LLDPE": "390190",
    "PP": "390210",
    "PET": "390760",
}

_DECLARATIONS: dict[str, dict[str, Any]] = {}

CLEARANCE_FLOW = ["draft", "submitted", "under_review", "inspection", "cleared", "rejected"]


def create_declaration(
    *,
    shipment_number: str,
    origin_port_code: str,
    customs_office: str,
    product_grade: str = "HDPE",
    quantity_tons: float = 100.0,
    value_usd: float = 100000.0,
    exporter: str = "Khalij Fars Holding",
    importer: str = "Overseas Buyer",
) -> dict[str, Any]:
    decl_no = f"IR{datetime.now(timezone.utc).strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    hs = GRADE_TO_HS.get(product_grade.upper(), "390120")
    now = datetime.now(timezone.utc).isoformat()
    decl = {
        "declaration_number": decl_no,
        "shipment_number": shipment_number,
        "origin_port_code": origin_port_code,
        "customs_office": customs_office,
        "hs_code": hs,
        "product_grade": product_grade.upper(),
        "quantity_tons": quantity_tons,
        "value_usd": value_usd,
        "regime": "export",
        "status": "draft",
        "status_history": [{"status": "draft", "at": now}],
        "exporter": exporter,
        "importer": importer,
        "epl_ref": f"EPL-{decl_no}",
        "integration": "customs.gov.ir/simulated",
        "cleared": False,
        "created_at": now,
        "updated_at": now,
    }
    decl["shipper"] = exporter
    decl["consignee"] = importer
    _DECLARATIONS[decl_no] = decl
    return decl


def advance_clearance(declaration_number: str, to_status: str | None = None) -> dict[str, Any]:
    decl = _DECLARATIONS.get(declaration_number)
    if not decl:
        raise KeyError(declaration_number)
    current = decl["status"]
    if to_status:
        if to_status not in CLEARANCE_FLOW:
            raise ValueError(f"invalid status: {to_status}")
        next_status = to_status
    else:
        idx = CLEARANCE_FLOW.index(current) if current in CLEARANCE_FLOW else 0
        if current in {"cleared", "rejected"}:
            next_status = current
        else:
            next_status = CLEARANCE_FLOW[min(idx + 1, CLEARANCE_FLOW.index("cleared"))]
    decl["status"] = next_status
    decl["status_history"].append({"status": next_status, "at": datetime.now(timezone.utc).isoformat()})
    decl["updated_at"] = datetime.now(timezone.utc).isoformat()
    decl["cleared"] = next_status == "cleared"
    _DECLARATIONS[declaration_number] = decl
    return decl


def get_declaration(declaration_number: str) -> dict[str, Any] | None:
    return _DECLARATIONS.get(declaration_number)


def by_shipment(shipment_number: str) -> list[dict[str, Any]]:
    return [d for d in _DECLARATIONS.values() if d["shipment_number"] == shipment_number]
