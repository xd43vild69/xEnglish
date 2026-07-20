"""Prueba de humo sin modelos: valida arranque, auth, DB y contrato de la API.

Ejecuta:  XENGLISH_SKIP_MODELS=1 .venv/bin/python smoke_test.py
Monkeypatchea el Pipeline para no cargar Whisper/LLM/TTS reales.
"""
import io
import os
import wave

os.environ["XENGLISH_SKIP_MODELS"] = "1"
os.environ["XENGLISH_API_KEY"] = "test-key"
os.environ["XENGLISH_DATA_DIR"] = "./data_test"
os.environ["XENGLISH_DB_URL"] = "sqlite+aiosqlite:///./data_test/test.db?nolock=1"

import numpy as np  # noqa: E402

from app.models.schemas import Explanation, GrammarIssue, LlmResult  # noqa: E402
from app.services import pipeline as pipeline_mod  # noqa: E402


# --- Fakes: reemplazan la inferencia real ---
async def fake_analyze(self, wav_path, context):
    result = LlmResult(
        corrected_text="I went to the store yesterday.",
        native_version="I ran to the store yesterday.",
        explanation=Explanation(
            grammar_issues=[GrammarIssue(error="i has went", fix="I went", rule="Past simple")],
            native_note="Un nativo diria 'ran' si fue rapido.",
            tips=["Capitaliza 'I'."],
        ),
    )
    return "i has went to the store yesterday", "en", result, {"whisper": 10, "llm": 20}


async def fake_synthesize(self, text, out_path):
    # WAV de silencio 0.2s @16k
    with wave.open(str(out_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes((np.zeros(3200, dtype=np.int16)).tobytes())
    return 5


pipeline_mod.Pipeline.analyze = fake_analyze
pipeline_mod.Pipeline.synthesize = fake_synthesize

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def make_wav_bytes() -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes((np.zeros(8000, dtype=np.int16)).tobytes())
    return buf.getvalue()


def main() -> None:
    with TestClient(app) as client:
        # health
        r = client.get("/api/v1/health")
        assert r.status_code == 200, r.text
        print("health:", r.json())

        # auth: sin key -> 401
        r = client.post("/api/v1/analyze", files={"audio": ("a.wav", b"x", "audio/wav")})
        assert r.status_code == 401, r.status_code
        print("auth sin key -> 401 OK")

        h = {"X-API-Key": "test-key"}
        wav = make_wav_bytes()

        # analyze
        r = client.post(
            "/api/v1/analyze",
            headers=h,
            files={"audio": ("a.wav", wav, "audio/wav")},
            data={"format": "wav"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        pid = body["id"]
        assert body["corrected_text"] == "I went to the store yesterday."
        assert body["audio_ready"] is False
        assert body["explanation"]["grammar_issues"][0]["fix"] == "I went"
        print("analyze OK ->", pid, body["processing_ms"])

        # detalle
        r = client.get(f"/api/v1/phrases/{pid}", headers=h)
        assert r.status_code == 200, r.text
        print("get phrase OK")

        # lista
        r = client.get("/api/v1/phrases", headers=h)
        assert r.status_code == 200 and r.json()["total"] >= 1, r.text
        print("list OK total=", r.json()["total"])

        # audio (dispara TTS fake)
        r = client.get(f"/api/v1/phrases/{pid}/audio", headers=h)
        assert r.status_code == 200 and r.headers["content-type"] == "audio/wav", r.text
        assert r.content[:4] == b"RIFF"
        print("audio TTS OK bytes=", len(r.content))

        # delete
        r = client.delete(f"/api/v1/phrases/{pid}", headers=h)
        assert r.status_code == 204, r.text
        r = client.get(f"/api/v1/phrases/{pid}", headers=h)
        assert r.status_code == 404
        print("delete OK")

    print("\n✅ TODOS LOS CHECKS PASARON")


if __name__ == "__main__":
    main()
