import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent
SONGS_DIR = BASE_DIR / "data" / "songs"
LYRICS_DIR = BASE_DIR / "data" / "lyrics"
PROCESSED_DIR = SONGS_DIR / "processed"
OUTPUT_DIR = SONGS_DIR / "align_song_json"
ALIGNMENT_URL = "https://api.elevenlabs.io/v1/forced-alignment"
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".aac", ".webm"}


def load_env():
    if load_dotenv:
        load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8-sig")


def find_audio_files():
    if not SONGS_DIR.exists():
        return []

    return sorted(
        path
        for path in SONGS_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS
    )


def find_lyrics_for_audio(audio_path):
    exact_match = LYRICS_DIR / f"{audio_path.stem}.txt"
    if exact_match.exists():
        return exact_match

    lyric_files = [
        path
        for path in LYRICS_DIR.glob("*.txt")
        if not path.name.endswith(".music.txt")
    ]
    if not lyric_files:
        raise RuntimeError(f"No lyric .txt file found in {LYRICS_DIR}")

    return max(lyric_files, key=lambda path: path.stat().st_mtime)


def read_lyrics(lyrics_path):
    text = lyrics_path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise RuntimeError(f"Lyrics file is empty: {lyrics_path}")
    return text


def call_elevenlabs_alignment(audio_path, lyrics_text):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Add ELEVENLABS_API_KEY=your-api-key to .env")

    with audio_path.open("rb") as audio_file:
        response = requests.post(
            ALIGNMENT_URL,
            headers={"xi-api-key": api_key},
            files={"file": (audio_path.name, audio_file, "application/octet-stream")},
            data={"text": lyrics_text},
            timeout=300,
        )

    if not response.ok:
        message = response.text.strip()[:500]
        raise RuntimeError(f"ElevenLabs alignment failed: {response.status_code} {message}")

    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError("ElevenLabs returned an unexpected response.")
    if not data.get("words"):
        raise RuntimeError("ElevenLabs returned no word timings.")
    return data


def make_line_timings(lyrics_text, words):
    lines = []
    word_index = 0

    for line_number, line in enumerate(lyrics_text.splitlines(), start=1):
        clean_line = line.strip()
        if not clean_line:
            continue

        line_words = clean_line.split()
        count = len(line_words)
        timed_words = words[word_index : word_index + count]
        word_index += count

        starts = [word.get("start") for word in timed_words if word.get("start") is not None]
        ends = [word.get("end") for word in timed_words if word.get("end") is not None]

        lines.append(
            {
                "line_number": line_number,
                "text": clean_line,
                "start": starts[0] if starts else None,
                "end": ends[-1] if ends else None,
                "words": timed_words,
            }
        )

    return lines


def count_lyric_words(lyrics_text):
    return sum(len(line.strip().split()) for line in lyrics_text.splitlines() if line.strip())


def save_alignment_json(audio_path, lyrics_path, lyrics_text, alignment, processed_audio_path):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{audio_path.stem}.alignment.json"
    if output_path.exists():
        raise RuntimeError(f"Alignment JSON already exists: {output_path}")

    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "audio_file": str(processed_audio_path),
        "original_audio_file": str(audio_path),
        "lyrics_file": str(lyrics_path),
        "lyrics_word_count": count_lyric_words(lyrics_text),
        "aligned_word_count": len(alignment.get("words", [])),
        "alignment_loss": alignment.get("loss"),
        "line_timings": make_line_timings(lyrics_text, alignment.get("words", [])),
        "raw_alignment": alignment,
    }

    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def move_to_processed(audio_path):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    destination = PROCESSED_DIR / audio_path.name
    if destination.exists():
        raise RuntimeError(f"Processed audio already exists: {destination}")

    shutil.move(str(audio_path), str(destination))
    return destination


def process_audio(audio_path):
    lyrics_path = find_lyrics_for_audio(audio_path)
    lyrics_text = read_lyrics(lyrics_path)
    processed_audio_path = PROCESSED_DIR / audio_path.name

    if processed_audio_path.exists():
        raise RuntimeError(f"Processed audio already exists: {processed_audio_path}")

    alignment = call_elevenlabs_alignment(audio_path, lyrics_text)
    output_path = save_alignment_json(
        audio_path,
        lyrics_path,
        lyrics_text,
        alignment,
        processed_audio_path,
    )
    moved_path = move_to_processed(audio_path)
    return output_path, moved_path, lyrics_path


def main():
    load_env()
    audio_files = find_audio_files()

    if not audio_files:
        print(f"No audio files found in {SONGS_DIR}")
        return 0

    failures = 0
    for audio_path in audio_files:
        try:
            output_path, moved_path, lyrics_path = process_audio(audio_path)
        except (OSError, requests.RequestException, RuntimeError, ValueError) as exc:
            failures += 1
            print(f"Error processing {audio_path.name}: {exc}")
            continue

        print(f"Aligned: {audio_path.name}")
        print(f"Lyrics: {lyrics_path}")
        print(f"JSON: {output_path}")
        print(f"Moved song: {moved_path}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
