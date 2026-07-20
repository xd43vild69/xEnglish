"""Orquestacion del pipeline con lock global de GPU (un request a la vez).

Contiene los servicios residentes (Whisper/LLM/TTS) cargados al startup.
"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

from app.config import Settings
from app.models.schemas import LlmResult
from app.services.asr import WhisperService
from app.services.llm import LlmService
from app.services.tts import TtsService


class Pipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.asr = WhisperService(settings)
        self.llm = LlmService(settings)
        self.tts = TtsService(settings)
        # Un solo request usa la GPU a la vez -> evita OOM en 12 GB.
        self._gpu_lock = asyncio.Lock()
        self._loaded = False

    def load_models(self) -> None:
        """Carga sincrona al startup (lifespan)."""
        self.asr.load()
        self.llm.load()
        self.tts.load()
        self._loaded = True

    @property
    def loaded(self) -> bool:
        return self._loaded

    async def analyze(
        self, wav_path: Path, context: str | None
    ) -> tuple[str, str, LlmResult, dict[str, int]]:
        """Whisper -> LLM. Devuelve (transcripcion, idioma, resultado, tiempos_ms)."""
        import os
        if os.getenv("XENGLISH_SKIP_MODELS") == "1":
            from app.models.schemas import Explanation, GrammarIssue, LlmResult
            mock_result = LlmResult(
                corrected_text="I went to the store yesterday.",
                native_version="I ran to the store yesterday.",
                explanation=Explanation(
                    grammar_issues=[GrammarIssue(error="i has went", fix="I went", rule="Past simple")],
                    native_note="Un nativo diria 'ran' si fue rapido.",
                    tips=["Capitaliza 'I'."],
                ),
            )
            return "i has went to the store yesterday", "en", mock_result, {"whisper": 10, "llm": 20}

        timings: dict[str, int] = {}
        async with self._gpu_lock:
            t0 = time.perf_counter()
            transcription, language = await asyncio.to_thread(
                self.asr.transcribe, wav_path
            )
            timings["whisper"] = int((time.perf_counter() - t0) * 1000)

            t1 = time.perf_counter()
            result = await asyncio.to_thread(self.llm.correct, transcription, context)
            timings["llm"] = int((time.perf_counter() - t1) * 1000)

        return transcription, language, result, timings

    async def synthesize(self, text: str, out_path: Path) -> int:
        """Genera audio TTS. Devuelve ms de procesamiento."""
        import os
        if os.getenv("XENGLISH_SKIP_MODELS") == "1":
            import wave
            import numpy as np
            with wave.open(str(out_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes((np.zeros(3200, dtype=np.int16)).tobytes())
            return 5

        async with self._gpu_lock:
            t0 = time.perf_counter()
            await asyncio.to_thread(self.tts.synthesize, text, out_path)
            return int((time.perf_counter() - t0) * 1000)
