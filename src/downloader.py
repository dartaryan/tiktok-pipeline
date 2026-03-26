"""Download audio from TikTok videos using yt-dlp."""

import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass

from .config import WORK_DIR


@dataclass
class VideoMeta:
    """Metadata extracted from the TikTok video."""
    video_id: str
    title: str
    creator: str
    duration: int  # seconds
    audio_path: Path
    source_url: str


def extract_video_id(url: str) -> str:
    """Extract the numeric video ID from a TikTok URL."""
    # Handles: tiktok.com/@user/video/123, vm.tiktok.com/ABC, etc.
    match = re.search(r"/video/(\d+)", url)
    if match:
        return match.group(1)
    # For short URLs, yt-dlp will resolve them — use a hash
    return re.sub(r"[^\w]", "_", url.split("/")[-1])[:32]


def download_audio(url: str) -> VideoMeta:
    """
    Download audio from a TikTok URL.
    Returns VideoMeta with the path to the audio file.
    """
    video_id = extract_video_id(url)

    # Step 1: Get metadata
    meta_cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        url,
    ]

    print(f"📥 Fetching metadata for {url}...")
    try:
        result = subprocess.run(
            meta_cmd, capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"yt-dlp metadata failed: {result.stderr}")
        meta = json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        raise RuntimeError("yt-dlp metadata timed out (60s)")

    title = meta.get("title", "untitled")
    creator = meta.get("uploader", meta.get("channel", "unknown"))
    duration = meta.get("duration", 0)
    video_id = meta.get("id", video_id)

    # Step 2: Check if audio was already extracted (skip re-download)
    audio_path = WORK_DIR / f"{video_id}.mp3"
    if audio_path.exists():
        print(f"♻️ Audio already exists, skipping download")
        return VideoMeta(
            video_id=video_id,
            title=title,
            creator=creator,
            duration=duration,
            audio_path=audio_path,
            source_url=url,
        )

    # Download — try multiple format strategies until we get audio
    video_path = WORK_DIR / f"{video_id}.mp4"

    format_attempts = [
        ("b", "single combined"),
        ("bv*+ba/b", "merge video+audio"),
        ("ba/b", "audio-only or combined"),
        (None, "default (no format flag)"),
    ]

    print(f"🎵 Downloading: {title} by @{creator} ({duration}s)...")

    downloaded = False
    for fmt, desc in format_attempts:
        # Clean previous attempt
        for f in WORK_DIR.glob(f"{video_id}.*"):
            f.unlink(missing_ok=True)

        download_cmd = [
            "yt-dlp",
            "--force-overwrites",
            "-o", str(video_path),
            "--no-playlist",
            url,
        ]
        if fmt:
            download_cmd.insert(1, "-f")
            download_cmd.insert(2, fmt)

        print(f"   Trying format: {desc}...")
        try:
            result = subprocess.run(
                download_cmd, capture_output=True, text=True, timeout=300
            )
            if result.returncode != 0:
                continue
        except subprocess.TimeoutExpired:
            continue

        # Find whatever file was downloaded
        candidates = list(WORK_DIR.glob(f"{video_id}.*"))
        media_files = [c for c in candidates if c.suffix in (".mp4", ".webm", ".mkv", ".m4a", ".mp3", ".ogg", ".opus")]
        if not media_files:
            continue
        video_path = media_files[0]

        # Check for audio stream
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-select_streams", "a",
            "-show_entries", "stream=codec_type",
            "-of", "csv=p=0",
            str(video_path),
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=30)
        if "audio" in probe_result.stdout:
            downloaded = True
            print(f"   ✅ Got audio with format: {desc}")
            break
        else:
            print(f"   ❌ No audio stream with format: {desc}")

    if not downloaded:
        raise RuntimeError(
            "Could not download a version with audio after trying all format options. "
            "This TikTok may have no spoken content."
        )

    # Step 3: Extract audio with ffmpeg
    audio_path = WORK_DIR / f"{video_id}.mp3"
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vn",                  # No video
        "-acodec", "libmp3lame",
        "-q:a", "5",           # Medium quality (good enough for speech)
        str(audio_path),
    ]

    print(f"🔊 Extracting audio...")
    try:
        result = subprocess.run(
            ffmpeg_cmd, capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg audio extraction failed: {result.stderr[-500:]}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("ffmpeg timed out (120s)")

    # Clean up the video file (we only need audio)
    video_path.unlink(missing_ok=True)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio extraction produced no output: {audio_path}")

    return VideoMeta(
        video_id=video_id,
        title=title,
        creator=creator,
        duration=duration,
        audio_path=audio_path,
        source_url=url,
    )


def cleanup(video_id: str):
    """Remove temporary audio files."""
    for f in WORK_DIR.glob(f"{video_id}.*"):
        f.unlink(missing_ok=True)
