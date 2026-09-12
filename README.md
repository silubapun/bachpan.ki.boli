# Kids Hindi Song Video Pipeline

Small Python workflow for creating Hindi children's song content for a YouTube channel.

The pipeline is split into simple files:

1. Generate Hindi lyrics from a topic, target age, and duration.
2. Put the manually generated song under `/data/songs`.
3. Generate a video brief and prompts for paid video tools.
4. Assemble generated clips with the song into a 1080p MP4.

By default the scripts use `/data`, matching your planned folder structure:

```text
/data/
  lyrics/
  songs/
  video_briefs/
  clips/
  final_videos/
  projects/
```

For local testing inside this repo, pass `--data-root ./data`.

## Requirements

- Python 3.10+
- FFmpeg and FFprobe installed and available in `PATH` for song validation and final video assembly.
- No third-party Python packages are required.

Check FFmpeg:

```bash
ffmpeg -version
ffprobe -version
```

## 1. Generate Lyrics

```bash
python scripts/generate_lyrics.py \
  --topic "space adventure" \
  --age 6 \
  --duration 90 \
  --data-root ./data
```

Output goes to:

```text
./data/lyrics/<slug>.txt
./data/lyrics/<slug>.json
```

On your production machine, omit `--data-root ./data` and it will save under `/data/lyrics`.

## 2. Add Song

Generate the song manually with Suno, ElevenLabs, or another tool. Save it under:

```text
/data/songs/
```

Then register/validate it:

```bash
python scripts/register_song.py \
  --song /data/songs/my_song.mp3 \
  --lyrics /data/lyrics/my_lyrics.txt
```

For local testing:

```bash
python scripts/register_song.py \
  --song ./data/songs/my_song.mp3 \
  --lyrics ./data/lyrics/my_lyrics.txt \
  --data-root ./data
```

## 3. Generate Video Brief

This creates scene ideas and prompts you can paste into paid video tools such as Runway, Pika, Luma, Kling, Kaiber, Canva, or similar services.

```bash
python scripts/generate_video_brief.py \
  --lyrics ./data/lyrics/my_lyrics.txt \
  --song ./data/songs/my_song.mp3 \
  --data-root ./data
```

Output:

```text
./data/video_briefs/<slug>.md
./data/video_briefs/<slug>.json
```

## 4. Assemble 1080p Video

Put generated clips for one song in a folder:

```text
/data/clips/my_song/
  01.mp4
  02.mp4
  03.mp4
```

Then assemble:

```bash
python scripts/assemble_video.py \
  --song /data/songs/my_song.mp3 \
  --clips-dir /data/clips/my_song
```

Local test example:

```bash
python scripts/assemble_video.py \
  --song ./data/songs/my_song.mp3 \
  --clips-dir ./data/clips/my_song \
  --data-root ./data
```

The final video is saved to:

```text
/data/final_videos/<song_name>_1080p.mp4
```

## Practical Tool Recommendation

For the paid-video step, do not over-engineer first. Start with one of these approaches:

- Fast experiment: Canva or CapCut templates plus generated clips/images.
- Better animated clips: Runway, Pika, Luma, Kling, or Kaiber.
- More control later: Blender/After Effects pipeline, but only after you know which song style gets views.

For the first 10-20 uploads, focus on testing topics, titles, thumbnails, and retention. Fancy automation is less important than finding what kids and parents actually replay.
