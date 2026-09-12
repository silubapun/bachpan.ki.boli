#!/usr/bin/env python3
"""Usage: python generate_lyrics.py (reads the local .env and sample JSON)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


def load_brief(path: Path) -> dict:
    """Load the complete brief and reject invalid inputs before calling OpenAI."""
    brief = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(brief, dict):
        raise ValueError("The JSON file must contain an object.")
    for key in ("audience", "song"):
        if not isinstance(brief.get(key), dict):
            raise ValueError(f"{key} is required and must be an object.")
    for key in ("music", "creative_constraints", "output"):
        if key in brief and not isinstance(brief[key], dict):
            raise ValueError(f"{key} must be an object.")

    song = brief["song"]
    for key in ("topic", "language"):
        if not isinstance(song.get(key), str) or not song[key].strip():
            raise ValueError(f"song.{key} must be nonempty text.")
    if "project_id" in brief and (
        not isinstance(brief["project_id"], str) or not brief["project_id"].strip()
    ):
        raise ValueError("project_id must be nonempty text.")

    audience = brief["audience"]
    age = audience.get("target_age")
    if type(age) is not int or not 4 <= age <= 12:
        raise ValueError("audience.target_age must be an integer from 4 to 12.")
    age_min, age_max = audience.get("age_min", 4), audience.get("age_max", 12)
    if (type(age_min) is not int or type(age_max) is not int
            or not 4 <= age_min <= age <= age_max <= 12):
        raise ValueError("Audience ages must satisfy 4 <= age_min <= target_age <= age_max <= 12.")
    duration = song.get("duration_seconds")
    if type(duration) is not int or not 20 <= duration <= 600:
        raise ValueError("song.duration_seconds must be an integer from 20 to 600.")

    structure = song.get("structure", {})
    if not isinstance(structure, dict):
        raise ValueError("song.structure must be an object.")
    constraints = brief.get("creative_constraints", {})
    for label, value in (
        ("song.structure.sections", structure.get("sections", [])),
        ("creative_constraints.must_include", constraints.get("must_include", [])),
        ("creative_constraints.avoid", constraints.get("avoid", [])),
    ):
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item.strip() for item in value
        ):
            raise ValueError(f"{label} must be a list of nonempty strings.")
    if "sections" in structure and not structure["sections"]:
        raise ValueError("song.structure.sections must not be empty when supplied.")
    if type(brief.get("output", {}).get("save_metadata", True)) is not bool:
        raise ValueError("output.save_metadata must be true or false.")
    return brief


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate song lyrics from a JSON brief using OpenAI.",
        epilog="Requires: pip install openai python-dotenv. Set OPENAI_API_KEY in .env next to this script.",
    )
    parser.add_argument("input_json", nargs="?", type=Path,
                        default=BASE_DIR / "json" / "lyrics_input.sample.json",
                        help="Optional JSON brief (default: json/lyrics_input.sample.json next to this script).")
    parser.add_argument("--data-root", type=Path, default=BASE_DIR / "data",
                        help="Output root; defaults to the data folder next to this script.")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL") or "gpt-4.1",
                        help="OpenAI model supporting Structured Outputs (default: OPENAI_MODEL or gpt-4.1).")
    return parser.parse_args()


def main() -> int:
    try:
        from dotenv import load_dotenv

        # Local settings take priority over values from an earlier shell session.
        load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8-sig")
        args = parse_args()
        brief = load_brief(args.input_json.expanduser())
        from lyrics_generator import generate_hindi_lyrics

        result = generate_hindi_lyrics(brief, args.data_root.expanduser() / "lyrics", args.model)
    except ImportError:
        print("Error: Install dependencies with: python -m pip install --upgrade openai python-dotenv", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Title: {result.title}")
    print(f"Lyrics: {result.lyrics_path}")
    print(f"Music directions: {result.music_path}")
    if result.metadata_path:
        print(f"Metadata: {result.metadata_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
