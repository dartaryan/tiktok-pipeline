"""Configuration and environment setup."""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Ensure ffmpeg is on PATH (Windows winget installs it outside PATH) ---
if not shutil.which("ffmpeg"):
    _winget_ffmpeg = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    for _candidate in _winget_ffmpeg.glob("*FFmpeg*/*/bin"):
        if (_candidate / "ffmpeg.exe").exists():
            os.environ["PATH"] = str(_candidate) + os.pathsep + os.environ.get("PATH", "")
            break

# --- API Keys ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# --- GitHub ---
GITHUB_REPO = os.getenv("GITHUB_REPO", "")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# --- GitHub Pages ---
# Auto-derive from GITHUB_REPO (e.g. "dartaryan/tiktok-knowledge" -> "https://dartaryan.github.io/tiktok-knowledge/")
# Override with GITHUB_PAGES_URL env var if using a custom domain.
_repo_parts = GITHUB_REPO.split("/", 1) if GITHUB_REPO else []
_default_pages_url = f"https://{_repo_parts[0]}.github.io/{_repo_parts[1]}/" if len(_repo_parts) == 2 else ""
GITHUB_PAGES_URL = os.getenv("GITHUB_PAGES_URL", _default_pages_url)

# --- Paths ---
WORK_DIR = Path(__file__).parent.parent / ".work"
WORK_DIR.mkdir(exist_ok=True)

# --- Instagram (cookies required for downloading) ---
# Path to a Netscape-format cookies.txt exported from your browser while logged into Instagram.
# Required for Instagram Reels. YouTube and TikTok work without cookies.
INSTAGRAM_COOKIES_FILE = os.getenv("INSTAGRAM_COOKIES_FILE", "")

# --- Claude Model ---
CLAUDE_MODEL = "claude-sonnet-4-6"

# --- Interest Categories ---
CATEGORIES = {
    "elon-katzef": {
        "he": "אלון קצף",
        "en": "Alon Katzef Advisory",
        "desc": "AI consulting and strategy for enterprise CEO. Covers AI adoption, governance, enterprise AI tools, Claude for business, insurtech, and organizational AI transformation.",
    },
    "shalhevet": {
        "he": "שלהבת",
        "en": "Shalhevet AI Training",
        "desc": "AI training facilitation and consulting business. Covers workshop design, prompt engineering teaching, AI literacy, hackathon facilitation, training pricing, and educational content creation.",
    },
    "taylor-played": {
        "he": "טיילור פלייד",
        "en": "TailorPlayed",
        "desc": "Custom board game studio — digital platform and physical products. Covers React/Vite/Firebase stack, e-commerce, Stripe, AliExpress sourcing, board game design, DaisyUI, Zustand, Gemini API, packaging, and small business ops.",
    },
    "optiplan": {
        "he": "אופטיפלן",
        "en": "OptiPlan",
        "desc": "Civil engineering project management SaaS. Covers React + TypeScript, Convex, NX monorepo, Clerk auth, Vercel, real-time collaboration, SaaS architecture, and full-stack TypeScript patterns.",
    },
    "other": {
        "he": "אחר",
        "en": "Other",
        "desc": "Content that doesn't clearly fit any of the four projects above.",
    },
}

# --- Category Emojis (for index) ---
CATEGORY_EMOJIS = {
    "elon-katzef": "🧠",
    "shalhevet": "🔥",
    "taylor-played": "🎲",
    "optiplan": "🏗️",
    "other": "📦",
}


def validate_config():
    """Check that all required env vars are set."""
    missing = []
    if not GROQ_API_KEY:
        missing.append("GROQ_API_KEY")
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not GITHUB_TOKEN:
        missing.append("GITHUB_TOKEN")
    if not GITHUB_REPO:
        missing.append("GITHUB_REPO")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Copy .env.example to .env and fill in your keys."
        )
