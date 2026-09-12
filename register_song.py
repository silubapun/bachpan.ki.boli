#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kids_channel.media import ffprobe_duration, is_audio
from kids_channel.paths import ensure_dirs, get_paths
from kids_channel.text_utils import slugify


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a generated song and create a project manifest.")
    parser.add_argument("--song", required=True, help="Song file path, usually under /data/songs.")
    parser.add_argument("--lyrics", default=None, help="Matching lyrics text file.")
    parser.add_argument("--data-root", default=None, help="Defaults to /data.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_paths(args.data_root)
    ensure_dirs(paths)

    song = Path(args.song).expanduser().resolve()
    if not song.exists():
        raise FileNotFoundError(f"Song file does not exist: {song}")
    if not is_audio(song):
        raise ValueError(f"Unsupported audio extension: {song.suffix}")

    lyrics = Path(args.lyrics).expanduser().resolve() if args.lyrics else None
    if lyrics and not lyrics.exists():
        raise FileNotFoundError(f"Lyrics file does not exist: {lyrics}")

    duration = ffprobe_duration(song)
    slug = slugify(song.stem, "song")
    manifest_path = paths.projects / f"{slug}.json"
    manifest_path.write_text(
        json.dumps(
            {
                "song": str(song),
                "lyrics": str(lyrics) if lyrics else None,
                "duration_seconds": round(duration, 2),
                "recommended_clips_dir": str(paths.clips / slug),
                "recommended_output": str(paths.final_videos / f"{slug}_1080p.mp4"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Song duration: {duration:.2f}s")
    print(f"Manifest: {manifest_path}")
    print(f"Put video clips here: {paths.clips / slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
