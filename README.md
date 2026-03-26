# TikTok Knowledge Pipeline 🎬→📝

Extract knowledge from English TikTok videos, translate to Hebrew, classify by topic, and save as structured markdown notes.

## Quick Start

```bash
# 1. Clone and install
cd tiktok-pipeline
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Install system dependencies
brew install yt-dlp ffmpeg  # macOS
# or: sudo apt install yt-dlp ffmpeg  # Linux

# 3. Set up API keys
cp .env.example .env
# Edit .env with your keys

# 4. Initialize GitHub repo structure
python pipeline.py --init

# 5. Process a video
python pipeline.py "https://www.tiktok.com/@user/video/123"

# Or test locally first (no GitHub push)
python pipeline.py "https://www.tiktok.com/@user/video/123" --local

# Batch process
python pipeline.py --batch urls.txt
```

## Required API Keys

| Key | Where to get it | Cost |
|-----|----------------|------|
| `GROQ_API_KEY` | [console.groq.com](https://console.groq.com) | Free |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) | ~$0.01-0.03/video |
| `GITHUB_TOKEN` | GitHub → Settings → Developer settings → PAT | Free |

## Pipeline Flow

```
TikTok URL → yt-dlp (audio) → Groq Whisper (transcript) → Claude (classify + translate + enrich) → GitHub (markdown)
```

## Project Structure

```
tiktok-pipeline/
├── pipeline.py          # CLI entry point
├── src/
│   ├── config.py        # Settings, categories, env vars
│   ├── downloader.py    # yt-dlp audio extraction
│   ├── transcriber.py   # Groq Whisper API
│   ├── processor.py     # Claude classification/translation
│   ├── formatter.py     # Markdown output formatting
│   └── storage.py       # GitHub API integration
├── .env.example
├── requirements.txt
└── README.md
```

## Customization

### Categories
Edit `src/config.py` → `CATEGORIES` dict to add/remove topic categories.

### Claude Prompt
The default prompt is in `src/processor.py` → `_build_system_prompt()`.
Replace it with your own Hebrew prompt for better results.

## Roadmap

- [x] Phase 1: CLI script (manual)
- [ ] Phase 2: Telegram bot
- [ ] Phase 3: Apple Shortcut input
- [ ] Phase 4: Weekly email digest
- [ ] Phase 5: Hebrew video support (Ivrit AI)
