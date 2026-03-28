"""Download audio from short-form video platforms using yt-dlp.

Supported platforms:
  - TikTok (tiktok.com, vm.tiktok.com)
  - Instagram Reels (instagram.com/reel/...) — requires cookies
  - YouTube / YouTube Shorts (youtube.com, youtu.be)
"""

import subprocess
import json
import re
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .config import WORK_DIR, INSTAGRAM_COOKIES_FILE


class Platform(Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    UNKNOWN = "unknown"


@dataclass
class VideoMeta:
    """Metadata extracted from the video."""
    video_id: str
    title: str
    creator: str
    duration: int  # seconds
    audio_path: Path
    source_url: str
    platform: Platform


# --- URL patterns per platform ---
_PLATFORM_PATTERNS: list[tuple[Platform, re.Pattern]] = [
    (Platform.TIKTOK, re.compile(
        r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/\S+'
    )),
    (Platform.INSTAGRAM, re.compile(
        r'https?://(?:www\.)?instagram\.com/(?:reel|reels|p)/\S+'
    )),
    (Platform.YOUTUBE, re.compile(
        r'https?://(?:www\.|m\.)?(?:youtube\.com/(?:watch|shorts|live)|youtu\.be/)\S*'
    )),
]

# Combined pattern — used by the bot to detect any supported link in a message
SUPPORTED_URL_PATTERN = re.compile(
    r'https?://(?:'
    r'(?:www\.|vm\.|vt\.)?tiktok\.com'
    r'|(?:www\.)?instagram\.com/(?:reel|reels|p)'
    r'|(?:www\.|m\.)?youtube\.com/(?:watch|shorts|live)'
    r'|youtu\.be'
    r')/\S+'
)


def detect_platform(url: str) -> Platform:
    """Detect which platform a URL belongs to."""
    for platform, pattern in _PLATFORM_PATTERNS:
        if pattern.match(url):
            return platform
    return Platform.UNKNOWN


def extract_video_id(url: str, platform: Platform) -> str:
    """Extract a usable video ID from a URL, per platform."""
    if platform == Platform.TIKTOK:
        match = re.search(r"/video/(\d+)", url)
        if match:
            return match.group(1)
    elif platform == Platform.INSTAGRAM:
        # instagram.com/reel/ABC123xyz/
        match = re.search(r"/(?:reel|reels|p)/([\w-]+)", url)
        if match:
            return match.group(1)
    elif platform == Platform.YOUTUBE:
        # youtube.com/shorts/VIDEO_ID, youtube.com/watch?v=VIDEO_ID, youtu.be/VIDEO_ID
        match = re.search(r"(?:shorts/|watch\?v=|youtu\.be/)([\w-]+)", url)
        if match:
            return match.group(1)
    # Fallback — hash the tail of the URL
    return re.sub(r"[^\w]", "_", url.split("/")[-1])[:32]


def _build_yt_dlp_base_args(platform: Platform, use_cookies: bool = False) -> list[str]:
    """Return extra yt-dlp arguments needed for a given platform."""
    args: list[str] = []
    if platform == Platform.INSTAGRAM and use_cookies:
        if INSTAGRAM_COOKIES_FILE and Path(INSTAGRAM_COOKIES_FILE).exists():
            args += ["--cookies", INSTAGRAM_COOKIES_FILE]
    return args


def download_audio(url: str) -> VideoMeta:
    """
    Download audio from a TikTok / Instagram Reel / YouTube video URL.
    Returns VideoMeta with the path to the audio file.
    """
    platform = detect_platform(url)
    video_id = extract_video_id(url, platform)
    # Try without cookies first; for Instagram, retry with cookies on failure
    platform_extra = _build_yt_dlp_base_args(platform, use_cookies=False)

    platform_label = platform.value.capitalize() if platform != Platform.UNKNOWN else "Video"

    # Step 1: Get metadata (try without cookies, retry with cookies for Instagram)
    print(f"  Fetching metadata for {platform_label} link...")
    meta = None
    for attempt, use_cookies in enumerate([False, True]):
        if attempt == 1:
            if platform != Platform.INSTAGRAM:
                break  # Only retry with cookies for Instagram
            cookies_args = _build_yt_dlp_base_args(platform, use_cookies=True)
            if not cookies_args:
                break  # No cookies file configured, nothing to retry with
            platform_extra = cookies_args
            print("  Retrying with Instagram cookies...")

        meta_cmd = [
            "yt-dlp",
            "--dump-json",
            "--no-download",
            *platform_extra,
            url,
        ]
        try:
            result = subprocess.run(
                meta_cmd, capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                meta = json.loads(result.stdout)
                break
            if attempt == 0 and platform == Platform.INSTAGRAM:
                continue  # Will retry with cookies
            raise RuntimeError(f"yt-dlp metadata failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            if attempt == 0 and platform == Platform.INSTAGRAM:
                continue
            raise RuntimeError("yt-dlp metadata timed out (60s)")

    if meta is None:
        raise RuntimeError(
            "Could not fetch metadata. For Instagram, make sure "
            "INSTAGRAM_COOKIES_FILE is set in .env (Netscape cookies.txt from Firefox)."
        )

    title = meta.get("title", "untitled")
    creator = meta.get("uploader", meta.get("channel", "unknown"))
    duration = meta.get("duration", 0)
    video_id = meta.get("id", video_id)

    # Step 2: Check if audio was already extracted (skip re-download)
    audio_path = WORK_DIR / f"{video_id}.mp3"
    if audio_path.exists():
        print(f"  Audio already cached, skipping download")
        return VideoMeta(
            video_id=video_id,
            title=title,
            creator=creator,
            duration=duration,
            audio_path=audio_path,
            source_url=url,
            platform=platform,
        )

    # Download — try multiple format strategies until we get audio
    video_path = WORK_DIR / f"{video_id}.mp4"

    format_attempts = [
        ("b", "single combined"),
        ("bv*+ba/b", "merge video+audio"),
        ("ba/b", "audio-only or combined"),
        (None, "default (no format flag)"),
    ]

    print(f"  Downloading: {title} by @{creator} ({duration}s)...")

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
            *platform_extra,
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
            print(f"   Got audio with format: {desc}")
            break
        else:
            print(f"   No audio stream with format: {desc}")

    if not downloaded:
        raise RuntimeError(
            f"Could not download a version with audio after trying all format options. "
            f"This {platform_label} video may have no spoken content."
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

    print(f"  Extracting audio...")
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
        platform=platform,
    )


def cleanup(video_id: str):
    """Remove temporary audio files."""
    for f in WORK_DIR.glob(f"{video_id}.*"):
        f.unlink(missing_ok=True)
