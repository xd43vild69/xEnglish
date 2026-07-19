"""Wrapper de TTS. Por defecto Piper (CPU, ~0 VRAM); opcion XTTS (GPU)."""
from __future__ import annotations

import wave
from pathlib import Path

from app.config import Settings


class TtsService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = None
        self._voice = None

    @property
    def model_name(self) -> str:
        if self._settings.tts_engine == "piper":
            return f"piper:{self._settings.piper_model_path.name}"
        return "xtts-v2"

    def load(self) -> None:
        if self._settings.tts_engine == "piper":
            from piper import PiperVoice  # import perezoso

            self._voice = PiperVoice.load(str(self._settings.piper_model_path))
            self._engine = "piper"
        else:
            from TTS.api import TTS  # coqui-tts

            self._voice = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
            self._engine = "xtts"

    def synthesize(self, text: str, out_path: Path) -> None:
        """Genera un WAV. Bloqueante: correr en threadpool."""
        if self._engine is None:
            raise RuntimeError("TtsService no cargado; llama a load() primero")

        if self._engine == "piper":
            with wave.open(str(out_path), "wb") as wf:
                self._voice.synthesize(text, wf)
        else:  # xtts
            self._voice.tts_to_file(
                text=text,
                file_path=str(out_path),
                language="en",
            )
