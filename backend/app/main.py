"""Punto de entrada FastAPI. Carga modelos en el lifespan (residentes)."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.config import get_settings
from app.db import init_db
from app.services.pipeline import Pipeline

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("xenglish")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db()

    pipeline = Pipeline(settings)
    app.state.pipeline = pipeline

    # Permite arrancar la API sin cargar modelos pesados (util para dev/tests).
    if os.getenv("XENGLISH_SKIP_MODELS") == "1":
        log.warning("XENGLISH_SKIP_MODELS=1 -> modelos NO cargados (modo dev)")
    else:
        log.info("Cargando modelos (Whisper, LLM, TTS)...")
        pipeline.load_models()
        log.info("Modelos cargados.")

    yield


app = FastAPI(title="xEnglish API", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "xEnglish", "docs": "/docs"}
