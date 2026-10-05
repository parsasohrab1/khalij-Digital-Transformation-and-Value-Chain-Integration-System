"""Invoice issuance and payment follow-up — memory + Postgres."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from shared.db import dumps, pg_execute, pg_fetchall, pg_fetchone

_INVOICES: dict[str, dict[str, Any]] = {}
_PAYMENTS: dict[str, dict[str, Any]] = {}
_HYDRATED = False


def _hydrate() -> None:
    global _HYDRATED
    if _HYDRATED:
        return
    for row in pg_fetchall("SELECT invoice_number, payload_json FROM invoices WHERE payload_json IS NOT NULL"):
        payload = row.get("payload_json") or {}
        if isinstance(payload, str):
            import json

            payload = json.loads(payload)
        if payload.get("invoice_number"):
            _INVOICES[payload["invoice_number"]] = payload
    for row in pg_fetchall("SELECT payment_number, payload_json FROM payments"):
        payload = row.get("payload_json") or {}
        if isinstance(payload, str):
            import json

            payload = json.loads(payload)
        if payload.get("payment_number"):
            _PAYMENTS[payload["payment_number"]] = payload
    _HYDRATED = True


def _persist_invoice(invoice: dict[str, Any]) -> None:
    pg_execute(
        """
        INSERT INTO invoices (invoice_number, amount_usd, currency, status, order_number, payload_json, order_id)
        VALUES (
            %s, %s, %s, %s, %s, %s::jsonb,
            (SELECT id FROM orders WHERE order_number = %s LIMIT 1)
        )
        ON CONFLICT (invoice_number) DO UPDATE SET
            status = EXCLUDED.status,
            amount_usd = EXCLUDED.amount_usd,
            order_number = EXCLUDED.order_number,
            payload_json = EXCLUDED.payload_json,
            paid_at = CASE WHEN EXCLUDED.status = 'paid' THEN now() ELSE invoices.paid_at END
        """,
        (
            invoice["invoice_number"],
            invoice["total_usd"],
            invoice.get("currency", "USD"),
            invoice.get("status", "issued"),
            invoice["order_number"],
            dumps(invoice),
            invoice["order_number"],
        ),
    )


def _persist_payment(payment: dict[str, Any]) -> None:
    pg_execute(
        """
        INSERT INTO payments (payment_number, invoice_number, amount_usd, method, reference, payload_json)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        ON CONFLICT (payment_number) DO UPDATE SET payload_json = EXCLUDED.payload_json
        """,
        (
            payment["payment_number"],
            payment["invoice_number"],
            payment["amount_usd"],
            payment.get("method", "wire"),
            payment.get("reference"),
            dumps(payment),
        ),
    )


def issue_invoice(
    *,
    order_number: str,
    amount_usd: float,
    currency: str = "USD",
    customer_name: str = "Customer",
    tax_pct: float = 0.0,
) -> dict[str, Any]:
    _hydrate()
    inv_no = f"INV-{uuid.uuid4().hex[:10].upper()}"
    tax = round(amount_usd * tax_pct / 100.0, 2)
    total = round(amount_usd + tax, 2)
    invoice = {
        "invoice_number": inv_no,
        "order_number": order_number,
        "amount_usd": amount_usd,
        "tax_usd": tax,
        "total_usd": total,
        "currency": currency,
        "customer_name": customer_name,
        "status": "issued",
        "payment_status": "unpaid",
        "paid_usd": 0.0,
        "erp_doc": f"FI-{inv_no}",
        "finance_system": "SAP-FI/simulated",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "paid_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _INVOICES[inv_no] = invoice
    _persist_invoice(invoice)
    return invoice


def record_payment(
    *,
    invoice_number: str,
    amount_usd: float,
    method: str = "wire",
    reference: str | None = None,
) -> dict[str, Any]:
    _hydrate()
    inv = _INVOICES.get(invoice_number) or (
        (pg_fetchone("SELECT payload_json FROM invoices WHERE invoice_number=%s", (invoice_number,)) or {}).get(
            "payload_json"
        )
    )
    if isinstance(inv, str):
        import json

        inv = json.loads(inv)
    if not inv:
        raise KeyError(invoice_number)
    if amount_usd <= 0:
        raise ValueError("amount must be positive")

    pay_no = f"PAY-{uuid.uuid4().hex[:8].upper()}"
    payment = {
        "payment_number": pay_no,
        "invoice_number": invoice_number,
        "order_number": inv["order_number"],
        "amount_usd": round(amount_usd, 2),
        "method": method,
        "reference": reference or f"TRX-{pay_no}",
        "status": "posted",
        "finance_system": "SAP-FI/simulated",
        "posted_at": datetime.now(timezone.utc).isoformat(),
    }
    _PAYMENTS[pay_no] = payment
    _persist_payment(payment)

    inv["paid_usd"] = round(float(inv.get("paid_usd") or 0) + amount_usd, 2)
    if inv["paid_usd"] + 1e-6 >= inv["total_usd"]:
        inv["payment_status"] = "paid"
        inv["status"] = "paid"
        inv["paid_at"] = payment["posted_at"]
    elif inv["paid_usd"] > 0:
        inv["payment_status"] = "partial"
        inv["status"] = "partially_paid"
    inv["updated_at"] = payment["posted_at"]
    _INVOICES[invoice_number] = inv
    _persist_invoice(inv)
    return {"payment": payment, "invoice": inv}


def get_invoice(invoice_number: str) -> dict[str, Any] | None:
    _hydrate()
    if invoice_number in _INVOICES:
        return _INVOICES[invoice_number]
    row = pg_fetchone("SELECT payload_json FROM invoices WHERE invoice_number=%s", (invoice_number,))
    if not row:
        return None
    payload = row["payload_json"]
    if isinstance(payload, str):
        import json

        payload = json.loads(payload)
    if payload:
        _INVOICES[invoice_number] = payload
    return payload


def invoices_for_order(order_number: str) -> list[dict[str, Any]]:
    _hydrate()
    mem = [i for i in _INVOICES.values() if i["order_number"] == order_number]
    if mem:
        return mem
    rows = pg_fetchall(
        "SELECT payload_json FROM invoices WHERE order_number=%s ORDER BY id DESC",
        (order_number,),
    )
    out = []
    for row in rows:
        payload = row["payload_json"]
        if isinstance(payload, str):
            import json

            payload = json.loads(payload)
        if payload:
            out.append(payload)
            _INVOICES[payload["invoice_number"]] = payload
    return out


def payments_for_invoice(invoice_number: str) -> list[dict[str, Any]]:
    _hydrate()
    mem = [p for p in _PAYMENTS.values() if p["invoice_number"] == invoice_number]
    if mem:
        return mem
    rows = pg_fetchall(
        "SELECT payload_json FROM payments WHERE invoice_number=%s ORDER BY id DESC",
        (invoice_number,),
    )
    out = []
    for row in rows:
        payload = row["payload_json"]
        if isinstance(payload, str):
            import json

            payload = json.loads(payload)
        if payload:
            out.append(payload)
            _PAYMENTS[payload["payment_number"]] = payload
    return out
