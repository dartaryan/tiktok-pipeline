# Transfer Document: TikTok Knowledge Pipeline — Handoff to Claude Code

> Paste this document into a Claude Code session inside the `tiktok-pipeline` repository directory. Claude Code should read all source files first, then continue from where this document left off.

---

## 1. CONTEXT

**Project:** TikTok Knowledge Extraction Pipeline ("tiktok-digest")
**Owner:** Ben (OptiPlansLabs founder, Israel, Windows PC)
**Repo location on disk:** `C:\Users\BenAkiva\Desktop\Tools\tiktok-digest\tiktok-pipeline\tiktok-pipeline`
**GitHub repo:** Already created and initialized with folder structure (elon-katzef/, shalhevet/, taylor-played/, optiplan/, other/, _weekly/, _queue/)

**What it does:** Takes TikTok video URLs → downloads audio (yt-dlp) → transcribes (Groq Whisper) → classifies + translates to Hebrew + enriches (Claude Sonnet 4.6 adaptive thinking with web search) → saves structured Hebrew markdown notes to GitHub repo → auto-generates README.md index.

**The pipeline is WORKING end-to-end.** It has been tested successfully with a real TikTok video. Local mode (`--local`) works. GitHub push mode works (folder init + note push + index generation).

---

## 2. DECISIONS MADE

- **Transcription:** Groq Whisper (free, fast). Ivrit AI deferred for future Hebrew video support.
- **Analysis model:** Claude Sonnet 4.6 with `thinking: { type: "adaptive" }`. Web search tool enabled for repo/tool URL verification. `effort` parameter was removed because the installed SDK version doesn't support it as a top-level arg (Sonnet 4.6 defaults to high anyway).
- **Categories:** 4 project-based categories (NOT generic tech topics): `elon-katzef`, `shalhevet`, `taylor-played`, `optiplan`, `other`. Full system prompt with detailed descriptions is in `src/processor.py`.
- **Output:** Hebrew markdown with YAML frontmatter. NO transcript included in output.
- **Storage:** GitHub repo with auto-generated README.md index (tables grouped by category, sorted newest first, with emojis and relevance stars).
- **Download strategy:** yt-dlp with a 4-format fallback chain (`b` → `bv*+ba/b` → `ba/b` → default), then ffprobe audio verification, then ffmpeg extraction. Required `curl_cffi` for TikTok impersonation.
- **Audio size:** Auto-shrink to 32kbps mono if >25MB (Groq limit).
- **Bot:** Telegram bot chosen over WhatsApp (WhatsApp needs Meta Business API). Bot built with `python-telegram-bot`.
- **Hosting:** Railway (Dockerfile ready). ~$5/month always-on.
- **Weekly digest:** Will be done via Cowork connecting to the repo (NOT Gmail).
- **Ben prefers:** English responses for technical/agent docs. Hebrew output in the pipeline itself. Direct, concrete answers.

---

## 3. CURRENT STATE

### What is COMPLETE and WORKING:
- `pipeline.py` — CLI entry point with `--local`, `--batch`, `--init` modes. Tested and working.
- `src/config.py` — Categories, emojis, env vars, model config. All set.
- `src/downloader.py` — yt-dlp with 4-format fallback + ffprobe check + ffmpeg extraction + audio cache. Working.
- `src/transcriber.py` — Groq Whisper with auto-shrink for large files. Working.
- `src/processor.py` — Claude Sonnet 4.6 adaptive thinking + web search. Full system prompt with project-based categories. Working.
- `src/formatter.py` — Markdown output with YAML frontmatter, no transcript. Working.
- `src/storage.py` — GitHub push + `update_index()` that generates README.md. Working.
- `bot.py` — Telegram bot that listens for TikTok URLs, processes them, pushes to GitHub. Written but NOT YET DEPLOYED.
- `Dockerfile` — Python 3.12-slim + ffmpeg. Ready.
- `railway.toml` — Railway deploy config. Ready.
- `.env.example` — Template with all required vars.
- `.dockerignore` — Excludes .env, .venv, .work, .git.
- `requirements.txt` — All deps including `python-telegram-bot>=21.0` and `curl_cffi>=0.7.0`.
- GitHub repo initialized with `--init` (folders created).
- One test note successfully pushed: `shalhevet/2026-03-26_claude-code-research-pipeline-chaining-skills-note.md`

### What is NOT yet done:
- Telegram bot NOT deployed to Railway yet
- Ben has the Telegram bot token from BotFather but has NOT added it to `.env` yet
- Weekly digest feature not built
- Batch processing not tested
- No CLAUDE.md or project docs in the repo yet

---

## 4. PENDING ITEMS (in priority order)

1. **Add TELEGRAM_BOT_TOKEN to .env** — Ben has the token, just needs to add it
2. **Test bot locally** — `python bot.py` to verify it works before deploying
3. **Push repo to GitHub** — `git init`, `git add .`, `git commit`, `git push` (make sure .env is gitignored!)
4. **Deploy to Railway** — Connect GitHub repo, add env vars, deploy
5. **Test end-to-end** — Send a TikTok link to the Telegram bot, verify note appears in GitHub repo
6. **Add ALLOWED_USER_IDS** — Lock bot to Ben's Telegram user ID (get from @userinfobot)
7. **Any improvements Ben wants to add** — he mentioned wanting to add more features

### Future items (not urgent):
- Weekly digest via Cowork
- Hebrew video support (Ivrit AI)
- Apple Shortcut input
- Batch processing from a queue file

---

## 5. KEY ARTIFACTS

### File structure:
```
tiktok-pipeline/
├── pipeline.py          # CLI entry point
├── bot.py               # Telegram bot
├── Dockerfile           # For Railway deployment
├── railway.toml         # Railway config
├── requirements.txt     # Python deps
├── .env.example         # Template
├── .env                 # Actual keys (gitignored)
├── .gitignore
├── .dockerignore
└── src/
    ├── __init__.py
    ├── config.py         # Categories, model, env vars
    ├── downloader.py     # yt-dlp + ffmpeg
    ├── transcriber.py    # Groq Whisper
    ├── processor.py      # Claude Sonnet 4.6 (SYSTEM PROMPT LIVES HERE)
    ├── formatter.py      # Markdown output
    └── storage.py        # GitHub API + index generation
```

### Environment variables needed:
```
GROQ_API_KEY=...
ANTHROPIC_API_KEY=...
GITHUB_TOKEN=...
GITHUB_REPO=username/tiktok-knowledge
GITHUB_BRANCH=main
TELEGRAM_BOT_TOKEN=...
ALLOWED_USER_IDS=...  (optional)
```

---

## 6. CONSTRAINTS AND PREFERENCES

- Windows PC (not Mac)
- Python 3.12+ with venv
- ffmpeg and yt-dlp installed globally and on PATH
- Ben communicates in Hebrew but wants English responses for technical work
- Pipeline output is in Hebrew (technical terms stay in English)
- Keep things simple and direct — Ben doesn't want over-engineering
- Use the existing file structure — don't reorganize unless asked

---

## 7. FIRST STEPS FOR CLAUDE CODE

When you receive this document:

1. Read all files in `src/` to understand the codebase
2. Confirm you understand the current state
3. Ask Ben what he wants to work on next — likely:
   - Finishing the deployment (adding bot token, testing, pushing to Railway)
   - Adding features or improvements
   - Fixing any issues that come up
4. Work directly in the repo files — you have full filesystem access
