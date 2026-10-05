"""AES-256-GCM encryption for sensitive data at rest (NFR-SEC-01)."""
from __future__ import annotations

import base64
import hashlib
import os
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from shared.settings import get_settings


def _key_bytes() -> bytes:
    settings = get_settings()
    raw = (getattr(settings, "aes_master_key", None) or settings.encryption_key or "").strip()
    try:
        key = bytes.fromhex(raw) if len(raw) in {32, 64} else raw.encode("utf-8")
    except ValueError:
        key = raw.encode("utf-8")
    if len(key) == 32:
        return key
    if len(key) == 16:
        # treat as hex of 16 bytes incorrectly; hash to 32
        return hashlib.sha256(key).digest()
    return hashlib.sha256(key).digest()


def encrypt_sensitive(plaintext: str, aad: bytes | None = None) -> str:
    """Output: base64(nonce || ciphertext+tag)."""
    aes = AESGCM(_key_bytes())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode("utf-8"), aad)
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def decrypt_sensitive(token: str, aad: bytes | None = None) -> str:
    raw = base64.urlsafe_b64decode(token.encode("ascii"))
    nonce, ct = raw[:12], raw[12:]
    aes = AESGCM(_key_bytes())
    return aes.decrypt(nonce, ct, aad).decode("utf-8")


def encrypt_json_fields(payload: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    out = dict(payload)
    for field in fields:
        if field in out and out[field] is not None:
            out[field] = encrypt_sensitive(str(out[field]), aad=field.encode())
            out[f"{field}_enc"] = True
    return out


def security_profile() -> dict[str, Any]:
    settings = get_settings()
    return {
        "at_rest": "AES-256-GCM",
        "in_transit": settings.tls_min_version,
        "force_https": settings.force_https,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "audit_log_enabled": settings.audit_log_enabled,
        "target_availability": settings.target_availability,
        "target_tps": settings.target_tps,
    }
