"""Wrapper del LLM local (llama.cpp) para correccion + refinamiento nativo.

Devuelve JSON estructurado validado contra `LlmResult`.
"""
from __future__ import annotations

import json

from app.config import Settings
from app.models.schemas import Explanation, LlmResult

_SYSTEM_ES = (
    "Eres un profesor de ingles experto. Recibes una frase que un estudiante "
    "dijo en ingles (transcrita, puede tener errores). Debes:\n"
    "1. Corregir la gramatica y ortografia (corrected_text).\n"
    "2. Dar la version que usaria un hablante nativo, natural y fluida (native_version).\n"
    "3. Explicar los errores de forma breve y clara EN ESPANOL.\n"
    "Responde UNICAMENTE con un objeto JSON valido, sin texto adicional, con esta forma:\n"
    '{"corrected_text": "...", "native_version": "...", '
    '"explanation": {"grammar_issues": [{"error":"...","fix":"...","rule":"..."}], '
    '"native_note": "...", "tips": ["..."]}}'
)

_SYSTEM_EN = (
    "You are an expert English teacher. You receive a phrase a student said in "
    "English (transcribed, may contain errors). You must:\n"
    "1. Correct grammar and spelling (corrected_text).\n"
    "2. Provide the version a native speaker would use (native_version).\n"
    "3. Briefly explain the errors in English.\n"
    "Respond ONLY with a valid JSON object, no extra text, of this shape:\n"
    '{"corrected_text": "...", "native_version": "...", '
    '"explanation": {"grammar_issues": [{"error":"...","fix":"...","rule":"..."}], '
    '"native_note": "...", "tips": ["..."]}}'
)


class LlmService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._llm = None

    @property
    def model_name(self) -> str:
        return self._settings.llm_model_path.name

    def load(self) -> None:
        from llama_cpp import Llama  # import perezoso

        s = self._settings
        self._llm = Llama(
            model_path=str(s.llm_model_path),
            n_gpu_layers=s.llm_n_gpu_layers,
            n_ctx=s.llm_n_ctx,
            verbose=False,
        )

    def _system_prompt(self) -> str:
        return _SYSTEM_ES if self._settings.explanation_lang == "es" else _SYSTEM_EN

    def correct(self, transcription: str, context: str | None = None) -> LlmResult:
        """Bloqueante: correr en threadpool."""
        if self._llm is None:
            raise RuntimeError("LlmService no cargado; llama a load() primero")

        user = f'Frase del estudiante: "{transcription}"'
        if context:
            user += f"\nContexto: {context}"

        resp = self._llm.create_chat_completion(
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=768,
            response_format={"type": "json_object"},  # JSON mode de llama.cpp
        )
        raw = resp["choices"][0]["message"]["content"]
        return self._parse(raw, transcription)

    @staticmethod
    def _parse(raw: str, fallback_text: str) -> LlmResult:
        try:
            data = json.loads(raw)
            return LlmResult.model_validate(data)
        except Exception:
            # Fallback defensivo si el modelo no respeta el formato
            return LlmResult(
                corrected_text=fallback_text,
                native_version=fallback_text,
                explanation=Explanation(
                    native_note="No se pudo generar el analisis estructurado.",
                    tips=[],
                ),
            )
