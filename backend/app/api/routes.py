"""Endpoints REST /api/v1."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_pipeline, require_api_key
from app.config import Settings, get_settings
from app.db import get_session
from app.models.db import Phrase
from app.models.schemas import (
    AnalyzeResponse,
    Explanation,
    GpuInfo,
    HealthResponse,
    PhraseListItem,
    PhraseListResponse,
)
from app.services.audio_utils import normalize_wav, wrap_pcm_to_wav
from app.services.pipeline import Pipeline

router = APIRouter(prefix="/api/v1")


def _gpu_info() -> GpuInfo:
    try:
        import pynvml  # opcional

        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        return GpuInfo(vram_used_mb=mem.used // 1024**2, vram_total_mb=mem.total // 1024**2)
    except Exception:
        return GpuInfo()


@router.get("/health", response_model=HealthResponse)
async def health(pipeline: Pipeline = Depends(get_pipeline)) -> HealthResponse:
    return HealthResponse(
        status="ok" if pipeline.loaded else "loading",
        gpu=_gpu_info(),
        models={
            "whisper": pipeline.asr.model_name,
            "llm": pipeline.llm.model_name,
            "tts": pipeline.tts.model_name,
        },
    )


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_api_key)],
)
async def analyze(
    audio: UploadFile,
    context: str | None = Form(default=None),
    sample_rate: int = Form(default=16000),
    fmt: str = Form(default="wav", alias="format"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    pipeline: Pipeline = Depends(get_pipeline),
) -> AnalyzeResponse:
    raw = await audio.read()
    if not raw:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Audio vacio")

    phrase = Phrase()
    orig_path = settings.audio_dir / f"{phrase.id}_orig.wav"

    # PCM crudo -> WAV, o WAV directo; luego normalizar a 16k mono.
    tmp_path = settings.audio_dir / f"{phrase.id}_in"
    if fmt == "pcm_s16le":
        wrap_pcm_to_wav(raw, sample_rate, tmp_path.with_suffix(".wav"))
        tmp_path = tmp_path.with_suffix(".wav")
    else:
        tmp_path = tmp_path.with_suffix(".wav")
        tmp_path.write_bytes(raw)

    sr, duration_ms = normalize_wav(tmp_path, orig_path)
    tmp_path.unlink(missing_ok=True)

    if duration_ms > settings.max_audio_seconds * 1000:
        orig_path.unlink(missing_ok=True)
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Audio supera {settings.max_audio_seconds}s",
        )

    transcription, language, result, timings = await pipeline.analyze(orig_path, context)

    phrase.original_audio_path = str(orig_path)
    phrase.sample_rate = sr
    phrase.duration_ms = duration_ms
    phrase.transcription = transcription
    phrase.corrected_text = result.corrected_text
    phrase.native_version = result.native_version
    phrase.explanation_json = result.explanation.model_dump_json()
    phrase.language = language
    phrase.whisper_model = pipeline.asr.model_name
    phrase.llm_model = pipeline.llm.model_name
    phrase.tts_model = pipeline.tts.model_name
    phrase.processing_ms_json = json.dumps(timings)

    session.add(phrase)
    await session.commit()

    return AnalyzeResponse(
        id=phrase.id,
        created_at=phrase.created_at,
        transcription=transcription,
        corrected_text=result.corrected_text,
        native_version=result.native_version,
        explanation=result.explanation,
        language=language,
        audio_ready=False,
        processing_ms=timings,
    )


@router.get(
    "/phrases",
    response_model=PhraseListResponse,
    dependencies=[Depends(require_api_key)],
)
async def list_phrases(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PhraseListResponse:
    total = await session.scalar(select(func.count()).select_from(Phrase))
    rows = await session.scalars(
        select(Phrase).order_by(Phrase.created_at.desc()).limit(limit).offset(offset)
    )
    items = [
        PhraseListItem(
            id=p.id,
            created_at=p.created_at,
            transcription=p.transcription,
            corrected_text=p.corrected_text,
            audio_ready=p.corrected_audio_path is not None,
        )
        for p in rows
    ]
    return PhraseListResponse(items=items, total=total or 0)


@router.get(
    "/phrases/{phrase_id}",
    response_model=AnalyzeResponse,
    dependencies=[Depends(require_api_key)],
)
async def get_phrase(
    phrase_id: str,
    session: AsyncSession = Depends(get_session),
) -> AnalyzeResponse:
    p = await session.get(Phrase, phrase_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe")
    return AnalyzeResponse(
        id=p.id,
        created_at=p.created_at,
        transcription=p.transcription,
        corrected_text=p.corrected_text,
        native_version=p.native_version,
        explanation=Explanation.model_validate_json(p.explanation_json),
        language=p.language,
        audio_ready=p.corrected_audio_path is not None,
        processing_ms=json.loads(p.processing_ms_json),
    )


@router.get("/phrases/{phrase_id}/audio", dependencies=[Depends(require_api_key)])
async def get_phrase_audio(
    phrase_id: str,
    variant: str = Query(default="corrected", pattern="^(corrected|native)$"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    pipeline: Pipeline = Depends(get_pipeline),
) -> FileResponse:
    p = await session.get(Phrase, phrase_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe")

    out_path = settings.audio_dir / f"{p.id}_{variant}.wav"
    if not out_path.exists():
        text = p.native_version if variant == "native" else p.corrected_text
        if not text:
            raise HTTPException(status.HTTP_409_CONFLICT, "Sin texto para sintetizar")
        await pipeline.synthesize(text, out_path)
        if variant == "corrected":
            p.corrected_audio_path = str(out_path)
            await session.commit()

    return FileResponse(out_path, media_type="audio/wav", filename=out_path.name)


@router.delete(
    "/phrases/{phrase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_api_key)],
)
async def delete_phrase(
    phrase_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    p = await session.get(Phrase, phrase_id)
    if p is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No existe")
    for path in (p.original_audio_path, p.corrected_audio_path):
        if path:
            Path(path).unlink(missing_ok=True)
    await session.delete(p)
    await session.commit()
