from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .models import SpeakerProfile


@dataclass
class MatchResult:
    speaker_id: str | None
    display_name: str | None
    similarity: float


def cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    denom = float(np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
    if denom == 0:
        return 0.0
    return float(np.dot(vector_a, vector_b) / denom)


def match_speaker(
    embedding: np.ndarray,
    profiles: list[SpeakerProfile],
    threshold: float,
) -> MatchResult:
    best = MatchResult(speaker_id=None, display_name=None, similarity=-1.0)
    for profile in profiles:
        similarity = cosine_similarity(embedding, np.asarray(profile.embedding, dtype=np.float32))
        if similarity > best.similarity:
            best = MatchResult(
                speaker_id=profile.speaker_id,
                display_name=profile.display_name,
                similarity=similarity,
            )
    if best.similarity < threshold:
        return MatchResult(speaker_id=None, display_name=None, similarity=best.similarity)
    return best
