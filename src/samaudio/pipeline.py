from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import numpy as np

from .audio import clip_audio
from .config import AppConfig, DEFAULT_CONFIG
from .diarization import diarize_audio
from .matcher import match_speaker
from .models import TranscriptSegment
from .speaker_embedding import embedding_from_audio
from .storage import ProfileStore
from .transcription import transcribe_audio


def _format_time(seconds: float) -> str:
    total_ms = int(seconds * 1000)
    hours, remainder = divmod(total_ms, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def process_meeting(
    meeting_audio: str,
    config: AppConfig = DEFAULT_CONFIG,
    language: str | None = "ja",
) -> tuple[Path, list[TranscriptSegment]]:
    store = ProfileStore(config)
    profiles = store.load_all_profiles()
    diarization = diarize_audio(meeting_audio)

    export_root = config.export_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    clips_dir = export_root / "clips"
    export_root.mkdir(parents=True, exist_ok=True)

    segments: list[TranscriptSegment] = []

    for index, (turn, _, speaker_label) in enumerate(diarization.itertracks(yield_label=True), start=1):
        start = float(turn.start)
        end = float(turn.end)
        duration = end - start
        if duration < config.min_segment_seconds:
            continue

        clip_path = clip_audio(meeting_audio, start, end, clips_dir / f"segment_{index:04d}.wav")
        embedding, _ = embedding_from_audio(clip_path)
        matched = match_speaker(
            embedding=np.asarray(embedding, dtype=np.float32),
            profiles=profiles,
            threshold=config.similarity_threshold,
        )

        transcript_items, _ = transcribe_audio(clip_path, language=language)
        text = " ".join(item.text.strip() for item in transcript_items).strip()
        speaker_name = matched.display_name or speaker_label
        confidence = matched.similarity if matched.speaker_id else None

        segments.append(
            TranscriptSegment(
                speaker_label=speaker_name,
                start=start,
                end=end,
                text=text,
                confidence=confidence,
                matched_profile=matched.speaker_id,
                similarity=matched.similarity,
            )
        )

    report_path = export_root / "meeting_report.json"
    report_path.write_text(
        json.dumps(
            {
                "meeting_audio": str(Path(meeting_audio).resolve()),
                "generated_at": datetime.now().isoformat(),
                "segments": [
                    {
                        **asdict(segment),
                        "start_ts": _format_time(segment.start),
                        "end_ts": _format_time(segment.end),
                    }
                    for segment in segments
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    markdown_path = export_root / "meeting_report.md"
    markdown_lines = [
        "# Meeting Report",
        "",
        f"- Source: {Path(meeting_audio).resolve()}",
        f"- Generated: {datetime.now().isoformat()}",
        "",
    ]
    for segment in segments:
        markdown_lines.append(
            f"- [{_format_time(segment.start)} - {_format_time(segment.end)}] "
            f"{segment.speaker_label}: {segment.text or '(no speech recognized)'}"
        )
    markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")

    return report_path, segments
