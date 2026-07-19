"""Wrapper de transcripcion con faster-whisper (carga perezosa)."""
from __future__ import annotations

from pathlib import Path

from app.config import Settings


class WhisperService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._model = None  # se carga en load()

    @property
    def model_name(self) -> str:
        return self._settings.whisper_model

    def load(self) -> None:
        """Carga el modelo en GPU. Llamar una vez al startup."""
        from faster_whisper import WhisperModel  # import perezoso

        s = self._settings
        self._model = WhisperModel(
            s.whisper_model,
            device=s.whisper_device,
            compute_type=s.whisper_compute_type,
        )

    def transcribe(self, wav_path: Path) -> tuple[str, str]:
        """Devuelve (texto, idioma). Bloqueante: correr en threadpool."""
        if self._model is None:
            raise RuntimeError("WhisperService no cargado; llama a load() primero")

        segments, info = self._model.transcribe(
            str(wav_path),
            language="en",
            vad_filter=True,
            beam_size=5,
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        return text, info.language
