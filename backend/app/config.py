"""Configuracion cargada desde variables de entorno / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="XENGLISH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Acceso
    api_key: str = "cambia-esta-clave"

    # Almacenamiento
    data_dir: Path = Path("./data")
    db_url: str = "sqlite+aiosqlite:///./data/xenglish.db"

    # Whisper
    whisper_model: str = "large-v3"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "int8_float16"

    # LLM
    llm_model_path: Path = Path("./models/qwen2.5-7b-instruct-q4_k_m.gguf")
    llm_n_gpu_layers: int = -1
    llm_n_ctx: int = 4096
    explanation_lang: str = "es"

    # TTS
    tts_engine: str = "piper"  # piper | xtts
    piper_model_path: Path = Path("./models/en_US-amy-medium.onnx")

    # Limites
    max_audio_seconds: int = 30

    @property
    def audio_dir(self) -> Path:
        return self.data_dir / "audio"

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.audio_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
