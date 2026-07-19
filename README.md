# xEnglish

App para mejorar tu ingles hablado. Grabas una frase, y la app te devuelve la
correccion gramatical, la version que usaria un nativo, una explicacion pedagogica
y el audio con la pronunciacion correcta.

**Todo local**: la inferencia (Whisper + LLM + TTS) corre en un servidor Linux con
una NVIDIA RTX 4070 Ti. El telefono solo captura audio y muestra la UI.

```
Android (Kotlin/Compose)  ──POST /analyze (WAV)──▶  Backend (FastAPI + GPU)
   AudioRecord, ExoPlayer  ◀──JSON: correccion────    Whisper → LLM → TTS
                           ◀──GET /audio (WAV)────     SQLite (historial)
```

## Componentes
- [`backend/`](backend/README.md) — FastAPI, faster-whisper, llama.cpp, Piper/XTTS, SQLite.
- [`android/`](android/README.md) — Kotlin, Jetpack Compose, Retrofit/OkHttp, Media3, Hilt.

## Arranque rapido (dev)
```bash
# Backend sin GPU (valida el contrato de la API):
cd backend && python -m venv .venv && source .venv/bin/activate
pip install fastapi "uvicorn[standard]" pydantic pydantic-settings python-multipart \
            SQLAlchemy aiosqlite greenlet numpy soundfile httpx
XENGLISH_SKIP_MODELS=1 python smoke_test.py   # prueba end-to-end con fakes
XENGLISH_SKIP_MODELS=1 uvicorn app.main:app --reload
```
El plan de arquitectura completo esta en el historial del proyecto.

## Decisiones de diseno
- **Single-user**: sin cuentas; auth por `X-API-Key`.
- **TTS bajo demanda**: `/analyze` responde rapido con texto; el audio se genera al pulsar "Escuchar".
- **Secuencial en GPU**: un `asyncio.Lock` evita OOM en los 12 GB de VRAM.
