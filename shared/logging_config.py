"""پیکربندی یکسان لاگ برای همه سرویس‌ها."""
import logging
import sys


def configure_logging(service_name: str, level: str = "INFO") -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=f"%(asctime)s | {service_name} | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
