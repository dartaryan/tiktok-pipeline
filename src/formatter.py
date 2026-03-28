"""Format processed notes as markdown files."""

from datetime import date
from slugify import slugify

from .processor import ProcessedNote


def to_markdown(note: ProcessedNote, source_url: str, creator: str, platform: str = "tiktok") -> str:
    """Convert a ProcessedNote to a markdown string with YAML frontmatter."""

    today = date.today().isoformat()
    tags_yaml = ", ".join(f'"{t}"' for t in note.tags)

    # --- Frontmatter ---
    md = f"""---
title_he: "{note.title_he}"
title_en: "{note.title_en}"
source: "{source_url}"
creator: "@{creator}"
platform: "{platform}"
category: "{note.category}"
relevance: {note.relevance}
date_processed: "{today}"
tags: [{tags_yaml}]
---

## תקציר

{note.summary_he}

"""

    # --- Key Insights ---
    if note.key_insights:
        md += "## תובנות מפתח\n\n"
        for insight in note.key_insights:
            md += f"- {insight}\n"
        md += "\n"

    # --- Tools & Libraries ---
    if note.tools_mentioned:
        md += "## כלים וספריות\n\n"
        md += "| שם | קישור | תיאור |\n"
        md += "|---|---|---|\n"
        for tool in note.tools_mentioned:
            name = tool.get("name", "—")
            url = tool.get("url", "—")
            desc = tool.get("desc_he", "—")
            link = f"[{name}]({url})" if url and url != "—" else name
            md += f"| {link} | {url} | {desc} |\n"
        md += "\n"

    # --- Repos ---
    if note.repos_mentioned:
        md += "## ריפוזיטוריז\n\n"
        for repo in note.repos_mentioned:
            md += f"- {repo}\n"
        md += "\n"

    # --- Action Items ---
    if note.action_items:
        md += "## פריטי פעולה\n\n"
        for item in note.action_items:
            md += f"- [ ] {item}\n"
        md += "\n"

    # --- Verification ---
    if note.verification_notes:
        md += "## הערות אימות\n\n"
        for v_note in note.verification_notes:
            md += f"- ⚠️ {v_note}\n"
        md += "\n"

    return md


def generate_filepath(note: ProcessedNote) -> str:
    """Generate the file path within the GitHub repo."""
    today = date.today().isoformat()
    slug = slugify(note.title_en, max_length=50)
    return f"{note.category}/{today}_{slug}.md"
