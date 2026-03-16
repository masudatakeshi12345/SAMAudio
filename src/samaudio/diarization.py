from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import torch
from pyannote.audio import Pipeline


@lru_cache(maxsize=1)
def get_diarization_pipeline() -> Pipeline:
    token = os.environ.get("HF_TOKEN")
    if not token:
        raise RuntimeError("HF_TOKEN is required for pyannote diarization models.")
    return Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=token,
    ).to(torch.device("cuda" if torch.cuda.is_available() else "cpu"))


def diarize_audio(audio_path: str | Path):
    pipeline = get_diarization_pipeline()
    return pipeline(str(audio_path))
