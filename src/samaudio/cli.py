from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from .config import DEFAULT_CONFIG
from .enrollment import enroll_speaker
from .pipeline import process_meeting
from .storage import ProfileStore


def _speaker_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-")
    if not normalized:
        raise argparse.ArgumentTypeError("speaker id must contain letters or numbers")
    return normalized


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="samaudio", description="SAMAudio CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    enroll_parser = subparsers.add_parser("enroll", help="Enroll a speaker from reference audio")
    enroll_parser.add_argument("--speaker-id", type=_speaker_id, required=True)
    enroll_parser.add_argument("--name", required=True)
    enroll_parser.add_argument("audio", nargs="+")

    meeting_parser = subparsers.add_parser("meeting", help="Process a meeting recording")
    meeting_parser.add_argument("audio")
    meeting_parser.add_argument("--language", default="ja")

    list_parser = subparsers.add_parser("list-speakers", help="List enrolled speakers")
    list_parser.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = ProfileStore(DEFAULT_CONFIG)

    if args.command == "enroll":
        profile = enroll_speaker(
            speaker_id=args.speaker_id,
            display_name=args.name,
            audio_paths=args.audio,
            store=store,
        )
        print(
            json.dumps(
                {
                    "speaker_id": profile.speaker_id,
                    "display_name": profile.display_name,
                    "samples": [sample.__dict__ for sample in profile.samples],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "meeting":
        report_path, segments = process_meeting(args.audio, language=args.language)
        print(
            json.dumps(
                {
                    "report_path": str(report_path),
                    "segment_count": len(segments),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "list-speakers":
        profiles = store.load_all_profiles()
        payload = [
            {
                "speaker_id": profile.speaker_id,
                "display_name": profile.display_name,
                "sample_count": len(profile.samples),
            }
            for profile in profiles
        ]
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for item in payload:
                print(f"{item['speaker_id']}\t{item['display_name']}\t{item['sample_count']}")
        return

    parser.error("unknown command")


if __name__ == "__main__":
    main()
