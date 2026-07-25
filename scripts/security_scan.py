"""Security checklist scanner for Phase 5 (NFR-SEC-01/02)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}{(' - ' + detail) if detail else ''}")
    return ok


def main() -> int:
    from shared.crypto import decrypt_sensitive, encrypt_sensitive, security_profile
    from shared.settings import get_settings

    settings = get_settings()
    results = []

    results.append(check("TLS min version is TLS 1.3", settings.tls_min_version.upper().replace("V", "v") in {"TLSv1.3", "TLS1.3"}))
    results.append(check("Audit logging enabled", settings.audit_log_enabled is True))
    results.append(check("Rate limit configured", settings.rate_limit_per_minute > 0, str(settings.rate_limit_per_minute)))
    results.append(check("Availability target 99.95%", settings.target_availability == "99.95%"))
    results.append(check("Horizontal scale target 50k TPS", settings.target_tps >= 50000, str(settings.target_tps)))

    token = encrypt_sensitive("contract-price-1000", aad=b"price")
    plain = decrypt_sensitive(token, aad=b"price")
    results.append(check("AES-256-GCM roundtrip", plain == "contract-price-1000", token[:24] + "..."))

    nginx = ROOT / "infra" / "nginx" / "nginx.conf"
    txt = nginx.read_text(encoding="utf-8") if nginx.exists() else ""
    results.append(check("Nginx enforces ssl_protocols TLSv1.3", "ssl_protocols TLSv1.3" in txt))

    prod = ROOT / "docker-compose.prod.yml"
    results.append(check("HA compose overlay exists", prod.exists()))

    profile = security_profile()
    print("profile=", profile)

    failed = sum(1 for r in results if not r)
    print(f"summary: {len(results) - failed}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
