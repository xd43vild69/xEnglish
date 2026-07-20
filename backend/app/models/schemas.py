from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

class GrammarIssue(BaseModel):
    error: str
    fix: str
    rule: str

class Explanation(BaseModel):
    grammar_issues: list[GrammarIssue] = Field(default_factory=list)
    native_note: str = ""
    tips: list[str] = Field(default_factory=list)

class LlmResult(BaseModel):
    corrected_text: str
    native_version: str
    explanation: Explanation

class GpuInfo(BaseModel):
    vram_used_mb: int | None = None
    vram_total_mb: int | None = None

class HealthResponse(BaseModel):
    status: str
    gpu: GpuInfo
    models: dict[str, str]

class AnalyzeResponse(BaseModel):
    id: str
    created_at: datetime
    transcription: str
    corrected_text: str
    native_version: str
    explanation: Explanation
    language: str
    audio_ready: bool
    processing_ms: dict[str, int] = Field(default_factory=dict)

class PhraseListItem(BaseModel):
    id: str
    created_at: datetime
    transcription: str
    corrected_text: str
    audio_ready: bool

class PhraseListResponse(BaseModel):
    items: list[PhraseListItem]
    total: int
