from __future__ import annotations

from pathlib import Path

import numpy as np
import soundfile as sf

from .models import EnrollmentSample, SpeakerProfile, path_str
from .speaker_embedding import embedding_from_audio
from .storage import ProfileStore


def enroll_speaker(
    speaker_id: str,
    display_name: str,
    audio_paths: list[str],
    store: ProfileStore,
) -> SpeakerProfile:
    embeddings: list[np.ndarray] = []
    samples: list[EnrollmentSample] = []
    sample_rate = 16000

    for audio_path in audio_paths:
        embedding, sample_rate = embedding_from_audio(audio_path)
        info = sf.info(audio_path)
        embeddings.append(embedding)
        samples.append(
            EnrollmentSample(
                path=path_str(Path(audio_path)),
                duration_seconds=float(info.duration),
            )
        )

    mean_embedding = np.mean(embeddings, axis=0)
    mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)
    profile = SpeakerProfile(
        speaker_id=speaker_id,
        display_name=display_name,
        embedding=mean_embedding.astype(np.float32).tolist(),
        sample_rate=sample_rate,
        samples=samples,
    )
    store.save_profile(profile)
    return profile
