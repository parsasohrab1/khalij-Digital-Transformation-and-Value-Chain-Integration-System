"""ثبت مدل در MLflow (با fallback محلی اگر سرور در دسترس نباشد)."""
from __future__ import annotations

import json
import logging
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from shared.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_LOCAL_REGISTRY: list[dict[str, Any]] = []
_REGISTRY_PATH = Path("data/ml_registry.json")
_MLFLOW_OK: bool | None = None


def _save_local() -> None:
    try:
        _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _REGISTRY_PATH.write_text(json.dumps(_LOCAL_REGISTRY[-50:], ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("local registry save failed: %s", exc)


def _mlflow_reachable() -> bool:
    global _MLFLOW_OK
    if os.getenv("MLFLOW_ENABLED", "true").lower() in {"0", "false", "no"}:
        _MLFLOW_OK = False
        return False
    if _MLFLOW_OK is not None:
        return _MLFLOW_OK
    try:
        parsed = urlparse(settings.mlflow_tracking_uri)
        host = parsed.hostname or "localhost"
        port = parsed.port or 5000
        with socket.create_connection((host, port), timeout=0.3):
            _MLFLOW_OK = True
    except OSError:
        _MLFLOW_OK = False
        logger.warning("MLflow unreachable; using local registry")
    return bool(_MLFLOW_OK)


def log_model_run(
    *,
    model_name: str,
    metrics: dict[str, float],
    params: dict[str, Any],
    tags: dict[str, str] | None = None,
) -> str:
    run_id = str(uuid.uuid4())
    entry = {
        "run_id": run_id,
        "model_name": model_name,
        "metrics": metrics,
        "params": params,
        "tags": tags or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "backend": "local",
    }

    if _mlflow_reachable():
        try:
            import mlflow

            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
            mlflow.set_experiment("khalij-dvc-supply-chain")
            with mlflow.start_run(run_name=f"{model_name}-{run_id[:8]}") as run:
                mlflow.log_params({k: str(v) for k, v in params.items()})
                mlflow.log_metrics(metrics)
                for k, v in (tags or {}).items():
                    mlflow.set_tag(k, v)
                run_id = run.info.run_id
                entry["run_id"] = run_id
                entry["backend"] = "mlflow"
        except Exception as exc:  # noqa: BLE001
            logger.warning("MLflow log failed, local registry used: %s", exc)

    _LOCAL_REGISTRY.append(entry)
    _save_local()
    return run_id


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    if _LOCAL_REGISTRY:
        return list(reversed(_LOCAL_REGISTRY[-limit:]))
    if _REGISTRY_PATH.exists():
        try:
            return list(reversed(json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))[-limit:]))
        except Exception:  # noqa: BLE001
            return []
    return []
