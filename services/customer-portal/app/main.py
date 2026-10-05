"""Customer self-service portal (FR-LOG-03) — without an internal login."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from shared.logging_config import configure_logging
from shared.settings import get_settings

settings = get_settings()
configure_logging("customer-portal", settings.log_level)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

app = FastAPI(title="Khalij DVC - Customer Portal", version="1.0.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "customer-portal", "phase": 6}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
