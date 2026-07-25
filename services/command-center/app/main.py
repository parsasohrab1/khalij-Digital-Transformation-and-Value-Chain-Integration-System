"""Command Center UI — پنل مدیریتی هلدینگ (فاز ۴)."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from shared.logging_config import configure_logging
from shared.settings import get_settings

settings = get_settings()
configure_logging("command-center", settings.log_level)
logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"

app = FastAPI(title="Khalij DVC - Command Center", version="4.0.0")
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "command-center", "phase": 4}


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
