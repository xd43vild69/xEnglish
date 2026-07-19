# xEnglish — Backend (FastAPI + GPU)

API REST que transcribe (Whisper), corrige/refina (LLM local) y sintetiza (TTS)
frases en ingles. Single-user, todo local sobre una RTX 4070 Ti (12 GB).

## Requisitos
- Linux con NVIDIA + CUDA (para produccion). En Mac/dev usa `XENGLISH_SKIP_MODELS=1`.
- Python 3.11+ (recomendado 3.11/3.12 para wheels de las libs de ML).
- Modelos descargados:
  - LLM GGUF (p.ej. `qwen2.5-7b-instruct-q4_k_m.gguf`) en `./models/`.
  - Voz Piper (`.onnx` + `.json`) en `./models/`.
  - Whisper `large-v3` se descarga solo la primera vez.

## Instalacion
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# CUDA para llama.cpp:
CMAKE_ARGS="-DGGML_CUDA=on" pip install --force-reinstall --no-cache-dir llama-cpp-python
cp .env.example .env   # y edita las rutas + API key
```

## Ejecutar
```bash
# Produccion (carga modelos en GPU):
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# Dev sin GPU/modelos (solo contrato de la API):
XENGLISH_SKIP_MODELS=1 uvicorn app.main:app --reload
```
Docs interactivas: http://localhost:8000/docs

## Prueba de humo (sin modelos)
```bash
XENGLISH_SKIP_MODELS=1 .venv/bin/python smoke_test.py
```

## Verificacion manual con curl
```bash
curl -F "audio=@sample.wav" -H "X-API-Key: <tu-key>" http://localhost:8000/api/v1/analyze
curl -H "X-API-Key: <tu-key>" http://localhost:8000/api/v1/phrases/<id>/audio -o out.wav
```

## Notas de rendimiento / VRAM (12 GB)
- Procesamiento **secuencial** con `asyncio.Lock` -> un request de GPU a la vez.
- Whisper `large-v3` int8_float16 (~4 GB) + LLM 7B Q4 (~5 GB) + Piper (CPU, 0 GB) ≈ 9 GB.
- TTS **bajo demanda** (`GET /phrases/{id}/audio`) -> baja la latencia percibida.
- `--workers 1`: un solo proceso comparte los modelos residentes.
