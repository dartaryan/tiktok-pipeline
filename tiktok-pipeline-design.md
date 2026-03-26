# TikTok Knowledge Extraction Pipeline — Design Document

## Overview

A personal automation pipeline that takes TikTok video links (English-language), extracts and structures the knowledge within, translates to Hebrew, classifies by relevance, and saves organized notes to a GitHub repository.

**Input:** Send a TikTok link via Telegram bot
**Output:** Structured Hebrew markdown note in a GitHub repo, categorized by topic

---

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Telegram    │────▶│  Download    │────▶│  Transcribe  │────▶│  Claude API  │────▶│  GitHub      │
│  Bot         │     │  (yt-dlp)    │     │  (Whisper)   │     │  Classify +  │     │  Repo        │
│              │     │              │     │              │     │  Translate   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                      │
                                                                      ▼
                                                               ┌──────────────┐
                                                               │  Web Search  │
                                                               │  (enrich)    │
                                                               └──────────────┘
```

---

## Component Breakdown

### 1. Input — Telegram Bot

**Why Telegram over WhatsApp:** Telegram has a free, well-documented bot API. WhatsApp Business API requires Meta approval and costs money. You can still forward TikTok links from WhatsApp → Telegram in one tap.

**Behavior:**
- You send a TikTok URL to the bot
- Bot acknowledges: `⏳ Processing...`
- When done: `✅ Saved: [title] → category`
- If it fails: `❌ Error: [reason]`

**Alternative input (Apple Shortcut):**
An iOS Shortcut can POST the shared URL to a webhook endpoint (the same server running the bot). This lets you share directly from the TikTok app → "Run Shortcut" without opening Telegram.

**Library:** `python-telegram-bot` (async, well-maintained)

---

### 2. Download — yt-dlp

Extract audio from the TikTok video. No need to download video since we only care about the spoken content.

```bash
yt-dlp -x --audio-format mp3 --audio-quality 5 \
  --cookies-from-browser chrome \
  -o "%(id)s.%(ext)s" \
  "https://www.tiktok.com/@user/video/123"
```

**Notes:**
- `--cookies-from-browser` may be needed if TikTok restricts access
- On a server without a browser, you'd export cookies once and use `--cookies cookies.txt`
- TikTok videos are short (15s–3min), so files are tiny
- If yt-dlp breaks on TikTok (it sometimes does), fallback to `tiktok-scraper` or a simple API proxy

---

### 3. Transcribe — Speech-to-Text

The TikTok videos are in **English**. Two recommended options:

#### Option A: Groq Whisper API (Recommended — Free & Fast)

Groq offers free Whisper large-v3 with extremely low latency.

```python
from groq import Groq

client = Groq(api_key="...")
with open("audio.mp3", "rb") as f:
    transcription = client.audio.transcriptions.create(
        file=("audio.mp3", f),
        model="whisper-large-v3-turbo",
        language="en"
    )
print(transcription.text)
```

- **Cost:** Free tier is generous for 4-10 short videos/week
- **Speed:** Fastest Whisper API available
- **Quality:** Whisper large-v3 is excellent for English

#### Option B: Ivrit AI (For Hebrew videos)

If you also want to process **Hebrew** TikTok videos in the future:

```python
import ivrit

model = ivrit.load_model(
    engine="runpod",
    model="ivrit-ai/whisper-large-v3-turbo-ct2",
    api_key="<your API key>",
    endpoint_id="<your endpoint ID>"
)
result = model.transcribe(path="audio.mp3", language="he")
```

- **Cost:** ~$0.03/hour via RunPod serverless
- **Setup:** Requires a RunPod account + deploying their Docker image
- **Best for:** Hebrew-language content specifically

#### Option C: OpenAI Whisper API

```python
from openai import OpenAI

client = OpenAI(api_key="...")
with open("audio.mp3", "rb") as f:
    transcription = client.audio.transcriptions.create(
        file=f,
        model="whisper-1"
    )
```

- **Cost:** $0.006/minute (~$0.01-0.02 per TikTok)
- **Reliable, well-documented**

**Recommendation:** Start with Groq (free). Add Ivrit AI later if you want Hebrew video support.

---

### 4. Classify + Translate + Enrich — Claude API

This is the brain of the pipeline. A single Claude API call takes the raw English transcript and produces the structured Hebrew output.

**What the prompt should contain (you write it, here's the spec):**

#### Prompt Structure Spec

```
┌─────────────────────────────────────────────────────┐
│ SYSTEM PROMPT                                        │
│                                                      │
│  1. ROLE DEFINITION                                  │
│     Who is this agent? A knowledge curator that       │
│     processes English tech video transcripts and      │
│     produces structured Hebrew knowledge notes.       │
│                                                      │
│  2. INTEREST CATEGORIES (you define these)            │
│     Each category needs:                              │
│     - Hebrew name                                     │
│     - English name                                    │
│     - 2-3 sentence description of what qualifies      │
│     - Example topics that belong here                 │
│                                                      │
│     Suggested starting set:                           │
│     • AI/LLM — כלי AI, סוכנים, פרומפטים, מודלים      │
│     • Frontend — React, UI, CSS, דפוסי עיצוב         │
│     • DevOps — CI/CD, תשתיות, Docker, ענן            │
│     • General Dev — ארכיטקטורה, דפוסי תכנות, כלים    │
│                                                      │
│  3. OUTPUT FORMAT (JSON or structured markdown)       │
│     Required fields:                                  │
│     - title_he: כותרת בעברית                          │
│     - title_en: Original English topic                │
│     - category: from predefined list                  │
│     - relevance: 1-5 (5 = must act on this)           │
│     - summary_he: 2-3 sentences, Hebrew               │
│     - key_insights: array of Hebrew bullet points     │
│     - tools_mentioned: array of objects:              │
│       { name (EN), url (if findable), desc_he }       │
│     - repos_mentioned: array of GitHub URLs           │
│     - action_items: what to try/look into (Hebrew)    │
│     - verification_notes: claims to double-check      │
│     - tags: free-form Hebrew tags for searchability   │
│                                                      │
│  4. LANGUAGE RULES                                    │
│     - Body text: Hebrew                               │
│     - Technical terms: English (React, Docker, etc.)  │
│     - Names of tools/repos/libraries: English         │
│     - Each English term gets a brief Hebrew context   │
│     - Links stay as-is                                │
│                                                      │
│  5. ENRICHMENT INSTRUCTIONS                           │
│     - If a GitHub repo is mentioned → find the URL    │
│     - If a tool is mentioned → find the official site │
│     - If a claim seems dubious → flag it              │
│     - If you know a better alternative → mention it   │
│                                                      │
│  6. EDGE CASES                                        │
│     - If transcript is too short/garbled → say so     │
│     - If content is promotional/spam → flag it        │
│     - If not relevant to any category → classify as   │
│       "other" with explanation                        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

#### Claude API Call

```python
import anthropic

client = anthropic.Anthropic(api_key="...")

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=4096,
    system=SYSTEM_PROMPT,  # Your prompt goes here
    messages=[{
        "role": "user",
        "content": f"""Process this TikTok video transcript:

Source URL: {tiktok_url}
Creator: {creator_name}
Duration: {duration}

Transcript:
{transcript_text}
"""
    }],
    # Optional: enable web search for enrichment
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search"
    }]
)
```

**Note:** Using Claude with web search tool enabled lets it verify claims and find repos in real-time.

---

### 5. Store — GitHub Repository

Save each processed video as a markdown file in a structured GitHub repo.

#### Repo Structure

```
tiktok-knowledge/
├── README.md                    # Auto-generated index
├── ai-llm/                     # Category folders
│   ├── 2026-03-26_cursor-ai-tips.md
│   └── 2026-03-24_claude-code-workflow.md
├── frontend/
│   └── 2026-03-25_react-19-patterns.md
├── devops/
│   └── 2026-03-23_github-actions-matrix.md
├── other/
│   └── ...
├── _queue/                      # Failed/pending items
│   └── ...
└── _weekly/                     # Weekly digests
    └── 2026-W13.md
```

#### Individual Note Format

```markdown
---
title_he: "טיפים מתקדמים ל-Cursor AI"
title_en: "Advanced Cursor AI Tips"
source: "https://www.tiktok.com/@user/video/123"
creator: "@user"
category: "ai-llm"
relevance: 4
date_processed: "2026-03-26"
tags: ["cursor", "ai-coding", "productivity"]
---

## תקציר
[2-3 sentence Hebrew summary]

## תובנות מפתח
- [insight 1]
- [insight 2]
- [insight 3]

## כלים וספריות
| שם | קישור | תיאור |
|---|---|---|
| Cursor | https://cursor.com | עורך קוד מבוסס AI |

## פריטי פעולה
- [ ] [actionable item in Hebrew]

## הערות אימות
- [any claims to verify]

---
*תמלול מקורי (אנגלית):*
> [collapsed/truncated original transcript]
```

#### GitHub API Integration

```python
import base64
from github import Github

g = Github("ghp_your_token")
repo = g.get_repo("your-username/tiktok-knowledge")

# Create file
repo.create_file(
    path=f"{category}/{date}_{slug}.md",
    message=f"Add: {title}",
    content=markdown_content,
    branch="main"
)
```

**Library:** `PyGithub`

---

### 6. Weekly Digest (Optional)

A cron job runs every Friday, collects all notes from the past week, and either:

**Option A: Gmail via API**
```python
# Use Gmail MCP or Google API to send a formatted email
# Subject: "📚 סיכום שבועי — TikTok Knowledge (W13)"
```

**Option B: GitHub Markdown**
Auto-generate a `_weekly/2026-W13.md` file summarizing the week's notes with links.

---

## Hosting & Deployment

### Recommended: Small VPS (Cheapest, Simplest)

| Provider | Spec | Cost |
|----------|------|------|
| Hetzner CX22 | 2 vCPU, 4GB RAM | ~€4/month |
| DigitalOcean | 1 vCPU, 1GB RAM | $6/month |
| Railway | Container | Free tier may suffice |

**Stack on VPS:**
- Python 3.12+
- systemd service for the Telegram bot (always-on)
- Cron job for weekly digest
- yt-dlp + ffmpeg installed

### Alternative: Serverless (More Complex, Potentially Free)

- Telegram webhook → Cloudflare Worker or Vercel Edge Function
- Processing → AWS Lambda or Google Cloud Function
- But: yt-dlp + ffmpeg are heavy dependencies for serverless

**Recommendation:** VPS. It's $4-6/month, dead simple, and you have full control.

---

## Cost Estimate (4-10 videos/week)

| Component | Cost |
|-----------|------|
| Groq Whisper | Free |
| Claude Sonnet API (~500 tokens in, ~2000 out per video) | ~$0.05-0.15/week |
| GitHub | Free |
| VPS (Hetzner) | ~€4/month |
| Telegram Bot | Free |
| **Total** | **~$5-7/month** |

---

## Implementation Order

1. **Phase 1 — Core Pipeline (Script)**
   Build a Python script you can run manually: paste URL → get markdown file.
   Test the transcription + Claude prompt quality.

2. **Phase 2 — Telegram Bot**
   Wrap the script in a Telegram bot. Deploy to VPS.

3. **Phase 3 — GitHub Integration**
   Auto-commit notes to the repo. Auto-generate README index.

4. **Phase 4 — Weekly Digest**
   Add cron job for email or weekly summary file.

5. **Phase 5 — Apple Shortcut (Optional)**
   iOS Shortcut that calls the same webhook endpoint for share-sheet integration.

---

## What You Need to Provide

1. **The Claude classification prompt** (in Hebrew) — see the spec in Section 4 above for what it should contain
2. **Telegram bot token** — create via @BotFather
3. **GitHub personal access token** — with repo write permissions
4. **Groq API key** — free at console.groq.com
5. **Claude/Anthropic API key** — for classification
6. **Your interest categories** — final list with Hebrew descriptions

---

## Open Questions

- **Do you want the Apple Shortcut as well, or is Telegram enough?**
- **Should the bot support batch processing?** (Send 5 links at once)
- **Do you want a "review before save" step?** (Bot shows summary, you approve before it commits to GitHub)
- **Should the weekly digest go to email, or just be a file in the repo?**
