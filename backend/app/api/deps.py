"""Dependencias comunes: auth por API key y acceso al pipeline."""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.services.pipeline import Pipeline


async def require_api_key(
    x_api_key: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not x_api_key or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key invalida o ausente",
        )


def get_pipeline(request: Request) -> Pipeline:
    pipeline: Pipeline | None = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline no inicializado",
        )
    return pipeline
