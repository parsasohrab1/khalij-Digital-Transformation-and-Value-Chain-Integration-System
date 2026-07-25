#!/usr/bin/env python
"""Generate self-signed TLS 1.3-compatible certs for local/prod-like nginx."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

OUT = Path(__file__).resolve().parents[1] / "infra" / "nginx" / "certs"
OUT.mkdir(parents=True, exist_ok=True)


def main() -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "IR"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Khalij Fars Holding"),
            x509.NameAttribute(NameOID.COMMON_NAME, "khalij-dvc.local"),
        ]
    )
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.DNSName("khalij-dvc.local")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    (OUT / "privkey.pem").write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    (OUT / "fullchain.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"wrote {OUT / 'fullchain.pem'} and privkey.pem")


if __name__ == "__main__":
    main()
