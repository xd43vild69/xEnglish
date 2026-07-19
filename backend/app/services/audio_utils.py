"""Utilidades de audio: normalizacion a WAV 16 kHz mono y metadatos."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

TARGET_SR = 16000


def wrap_pcm_to_wav(pcm_bytes: bytes, sample_rate: int, out_path: Path) -> None:
    """Envuelve PCM crudo (int16 LE, mono) en un archivo WAV."""
    data = np.frombuffer(pcm_bytes, dtype=np.int16)
    sf.write(out_path, data, sample_rate, subtype="PCM_16")


def normalize_wav(in_path: Path, out_path: Path) -> tuple[int, int]:
    """Convierte a mono 16 kHz PCM16. Devuelve (sample_rate, duration_ms)."""
    data, sr = sf.read(in_path, dtype="float32", always_2d=True)
    # mono: promedio de canales
    if data.shape[1] > 1:
        data = data.mean(axis=1, keepdims=True)
    data = data[:, 0]

    if sr != TARGET_SR:
        data = _resample_linear(data, sr, TARGET_SR)
        sr = TARGET_SR

    sf.write(out_path, data, sr, subtype="PCM_16")
    duration_ms = int(len(data) / sr * 1000)
    return sr, duration_ms


def _resample_linear(data: np.ndarray, src_sr: int, dst_sr: int) -> np.ndarray:
    """Resample simple por interpolacion lineal (suficiente para voz mono).

    Para produccion se recomienda `soxr` o `librosa.resample`.
    """
    if src_sr == dst_sr:
        return data
    duration = len(data) / src_sr
    dst_len = int(duration * dst_sr)
    if dst_len <= 0:
        return data
    src_idx = np.linspace(0, len(data) - 1, num=dst_len)
    return np.interp(src_idx, np.arange(len(data)), data).astype(np.float32)
