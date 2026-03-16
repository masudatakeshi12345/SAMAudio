from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class EnrollmentSample:
    path: str
    duration_seconds: float


@dataclass
class SpeakerProfile:
    speaker_id: str
    display_name: str
    embedding: list[float]
    sample_rate: int
    samples: list[EnrollmentSample] = field(default_factory=list)


@dataclass
class TranscriptSegment:
    speaker_label: str
    start: float
    end: float
    text: str
    confidence: float | None = None
    matched_profile: str | None = None
    similarity: float | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


def path_str(path: Path) -> str:
    return str(path.resolve())
