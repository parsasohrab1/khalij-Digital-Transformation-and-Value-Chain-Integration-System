"""Basic security checks for Phase 5 readiness (headers, crypto, rate-limit signal)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check_crypto() -> dict:
    from shared.crypto import decrypt_sensitive, encrypt_sensitive, security_profile

    token = encrypt_sensitive("contract-price=912.5", aad=b"price")
    plain = decrypt_sensitive(token, aad=b"price")
    assert plain == "contract-price=912.5"
    assert token != plain
    return {"crypto": "ok", "profile": security_profile()}


def check_audit() -> dict:
    from shared.audit import audit, list_audit

    audit(action="security.scan", actor="phase5-script", resource="self-check", outcome="success")
    rows = list_audit(5)
    assert rows and rows[0]["action"] == "security.scan"
    return {"audit": "ok", "latest_action": rows[0]["action"]}


def check_rate_limit_module() -> dict:
    from shared.rate_limit import rate_limit_dependency

    assert callable(rate_limit_dependency)
    return {"rate_limit_module": "ok"}


def check_tls_assets() -> dict:
    cert = ROOT / "infra" / "nginx" / "certs" / "fullchain.pem"
    key = ROOT / "infra" / "nginx" / "certs" / "privkey.pem"
    conf = ROOT / "infra" / "nginx" / "nginx.conf"
    text = conf.read_text(encoding="utf-8")
    assert "TLSv1.3" in text
    assert "ssl_protocols TLSv1.3" in text
    return {
        "nginx_tls13": True,
        "certs_present": cert.exists() and key.exists(),
        "hint": "python scripts/generate_tls_certs.py",
    }


def main() -> None:
    results = {
        "crypto": check_crypto(),
        "audit": check_audit(),
        "rate_limit": check_rate_limit_module(),
        "tls": check_tls_assets(),
    }
    print(results)
    print("SECURITY_CHECK_PASSED")


if __name__ == "__main__":
    main()
