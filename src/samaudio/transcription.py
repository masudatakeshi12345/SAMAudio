from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel


@lru_cache(maxsize=1)
def get_whisper_model(model_size: str = "small") -> WhisperModel:
    return WhisperModel(
        model_size,
        device="cuda" if __import__("torch").cuda.is_available() else "cpu",
        compute_type="float16" if __import__("torch").cuda.is_available() else "int8",
    )


def transcribe_audio(path: str | Path, language: str | None = "ja"):
    model = get_whisper_model()
    segments, info = model.transcribe(str(path), language=language, vad_filter=True)
    return list(segments), info
