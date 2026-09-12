#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kids_channel.assembler import assemble_1080p_video
from kids_channel.paths import ensure_dirs, get_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Match generated clips to a song and produce a 1080p video.")
    parser.add_argument("--song", required=True, help="Song audio file.")
    parser.add_argument("--clips-dir", required=True, help="Folder containing clips/images in playback order.")
    parser.add_argument("--output", default=None, help="Optional output MP4 path.")
    parser.add_argument("--fps", type=int, default=30, help="Output FPS.")
    parser.add_argument("--data-root", default=None, help="Defaults to /data.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = get_paths(args.data_root)
    ensure_dirs(paths)
    result = assemble_1080p_video(
        song_path=args.song,
        clips_dir=args.clips_dir,
        paths=paths,
        output_path=args.output,
        fps=args.fps,
    )
    print(f"Final video: {result.output_path}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Clips used: {result.clip_count}")
    print(f"Duration: {result.duration_seconds:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
