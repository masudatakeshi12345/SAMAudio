from __future__ import annotations

import json
from pathlib import Path

from .config import AppConfig, DEFAULT_CONFIG
from .models import SpeakerProfile


class ProfileStore:
    def __init__(self, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.config = config
        self.config.enrollment_dir.mkdir(parents=True, exist_ok=True)
        self.config.export_dir.mkdir(parents=True, exist_ok=True)

    def profile_path(self, speaker_id: str) -> Path:
        return self.config.enrollment_dir / f"{speaker_id}.json"

    def save_profile(self, profile: SpeakerProfile) -> Path:
        path = self.profile_path(profile.speaker_id)
        path.write_text(
            json.dumps(
                {
                    "speaker_id": profile.speaker_id,
                    "display_name": profile.display_name,
                    "embedding": profile.embedding,
                    "sample_rate": profile.sample_rate,
                    "samples": [
                        {
                            "path": sample.path,
                            "duration_seconds": sample.duration_seconds,
                        }
                        for sample in profile.samples
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return path

    def load_profile(self, speaker_id: str) -> SpeakerProfile:
        path = self.profile_path(speaker_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        return SpeakerProfile(**payload)

    def load_all_profiles(self) -> list[SpeakerProfile]:
        profiles: list[SpeakerProfile] = []
        for path in sorted(self.config.enrollment_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            profiles.append(SpeakerProfile(**payload))
        return profiles
