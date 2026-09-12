#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kids_channel.paths import ensure_dirs, get_paths
from kids_channel.video_brief import create_video_brief


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate video prompts/brief from lyrics.")
    parser.add_argument("--lyrics", required=True, help="Lyrics text file.")
    parser.add_argument("--song", default=None, help="Optional song file; used for exact timing.")
    parser.add_argument("--scene-count", type=int, default=8, help="Number of scenes/prompts, 3 to 16.")
    parser.add_argument("--data-root", default=None, help="Defaults to /data.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_paths(args.data_root)
    ensure_dirs(paths)
    result = create_video_brief(
        lyrics_path=args.lyrics,
        song_path=args.song,
        paths=paths,
        scene_count=args.scene_count,
    )
    print(f"Video brief: {result.markdown_path}")
    print(f"Brief JSON: {result.json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
