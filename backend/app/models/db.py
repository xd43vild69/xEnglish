from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def generate_uuid() -> str:
    return str(uuid.uuid4())

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Phrase(Base):
    __tablename__ = "phrases"

    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    original_audio_path = Column(String, nullable=True)
    corrected_audio_path = Column(String, nullable=True)
    sample_rate = Column(Integer, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    transcription = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    native_version = Column(Text, nullable=False)
    explanation_json = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    whisper_model = Column(String, nullable=False)
    llm_model = Column(String, nullable=False)
    tts_model = Column(String, nullable=False)
    processing_ms_json = Column(Text, nullable=False)
