"""صدور فاکتور و پیگیری پرداخت — آداپتر مالی/ERP شبیه‌سازی‌شده."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

_INVOICES: dict[str, dict[str, Any]] = {}
_PAYMENTS: dict[str, dict[str, Any]] = {}

PAYMENT_STATUSES = ["unpaid", "pending", "partial", "paid", "failed", "refunded"]


def issue_invoice(
    *,
    order_number: str,
    amount_usd: float,
    currency: str = "USD",
    customer_name: str = "Customer",
    tax_pct: float = 0.0,
) -> dict[str, Any]:
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
    return invoice


def record_payment(
    *,
    invoice_number: str,
    amount_usd: float,
    method: str = "wire",
    reference: str | None = None,
) -> dict[str, Any]:
    inv = _INVOICES.get(invoice_number)
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

    inv["paid_usd"] = round(float(inv["paid_usd"]) + amount_usd, 2)
    if inv["paid_usd"] + 1e-6 >= inv["total_usd"]:
        inv["payment_status"] = "paid"
        inv["status"] = "paid"
        inv["paid_at"] = payment["posted_at"]
    elif inv["paid_usd"] > 0:
        inv["payment_status"] = "partial"
        inv["status"] = "partially_paid"
    inv["updated_at"] = payment["posted_at"]
    _INVOICES[invoice_number] = inv
    return {"payment": payment, "invoice": inv}


def get_invoice(invoice_number: str) -> dict[str, Any] | None:
    return _INVOICES.get(invoice_number)


def invoices_for_order(order_number: str) -> list[dict[str, Any]]:
    return [i for i in _INVOICES.values() if i["order_number"] == order_number]


def payments_for_invoice(invoice_number: str) -> list[dict[str, Any]]:
    return [p for p in _PAYMENTS.values() if p["invoice_number"] == invoice_number]
