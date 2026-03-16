import numpy as np

from samaudio.matcher import cosine_similarity, match_speaker
from samaudio.models import SpeakerProfile


def test_cosine_similarity_returns_one_for_identical_vectors():
    vector = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert cosine_similarity(vector, vector) == 1.0


def test_match_speaker_returns_best_profile_above_threshold():
    embedding = np.array([1.0, 0.0], dtype=np.float32)
    profiles = [
        SpeakerProfile("alice", "Alice", [1.0, 0.0], 16000),
        SpeakerProfile("bob", "Bob", [0.0, 1.0], 16000),
    ]

    result = match_speaker(embedding, profiles, threshold=0.7)

    assert result.speaker_id == "alice"
    assert result.display_name == "Alice"
    assert result.similarity == 1.0


def test_match_speaker_returns_unknown_when_similarity_below_threshold():
    embedding = np.array([1.0, 0.0], dtype=np.float32)
    profiles = [SpeakerProfile("bob", "Bob", [0.0, 1.0], 16000)]

    result = match_speaker(embedding, profiles, threshold=0.1)

    assert result.speaker_id is None
    assert result.display_name is None
