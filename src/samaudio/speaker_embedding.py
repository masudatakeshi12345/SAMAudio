from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import torch
from speechbrain.inference.speaker import EncoderClassifier

from .audio import TARGET_SAMPLE_RATE, load_audio


@lru_cache(maxsize=1)
def get_encoder() -> EncoderClassifier:
    return EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        savedir="pretrained_models/spkrec-ecapa-voxceleb",
        run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    )


def embedding_from_audio(path: str | Path) -> tuple[np.ndarray, int]:
    classifier = get_encoder()
    waveform, sample_rate = load_audio(path, TARGET_SAMPLE_RATE)
    embedding = classifier.encode_batch(waveform).squeeze().detach().cpu().numpy()
    normalized = embedding / np.linalg.norm(embedding)
    return normalized.astype(np.float32), sample_rate
