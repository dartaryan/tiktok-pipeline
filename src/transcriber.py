"""Transcribe audio using Groq's Whisper API."""

import subprocess
from pathlib import Path
from groq import Groq

from .config import GROQ_API_KEY

MAX_FILE_SIZE_MB = 25  # Groq Whisper limit


def _shrink_audio(audio_path: Path) -> Path:
    """Re-encode audio at lower bitrate to fit within API limits."""
    shrunk_path = audio_path.with_stem(audio_path.stem + "_small")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_path),
        "-acodec", "libmp3lame",
        "-b:a", "32k",       # Low bitrate — fine for speech
        "-ar", "16000",      # 16kHz sample rate — standard for ASR
        "-ac", "1",          # Mono
        str(shrunk_path),
    ]
    print(f"📦 Audio too large ({audio_path.stat().st_size // 1024 // 1024}MB), re-encoding...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg re-encode failed: {result.stderr[-300:]}")
    print(f"   Shrunk to {shrunk_path.stat().st_size // 1024 // 1024}MB")
    return shrunk_path


def transcribe(audio_path: Path, language: str = "en") -> str:
    """
    Transcribe an audio file using Groq Whisper.

    Args:
        audio_path: Path to the audio file (mp3, m4a, wav, etc.)
        language: Language code ("en" for English, "he" for Hebrew)

    Returns:
        Transcribed text as a string.
    """
    # Check file size — Groq limit is 25MB
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        audio_path = _shrink_audio(audio_path)

    client = Groq(api_key=GROQ_API_KEY)

    print(f"🎙️ Transcribing {audio_path.name} ({file_size_mb:.1f}MB, language={language})...")

    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(audio_path.name, f),
            model="whisper-large-v3-turbo",
            language=language,
            response_format="text",
        )

    text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()

    word_count = len(text.split())
    print(f"✅ Transcribed: {word_count} words")

    if word_count < 5:
        raise ValueError(
            f"Transcription too short ({word_count} words). "
            f"The audio may be music-only, silent, or corrupted."
        )

    return text
