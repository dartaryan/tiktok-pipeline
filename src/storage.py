"""Store processed notes in a GitHub repository."""

import re
from datetime import datetime
from github import Github, GithubException

from .config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_BRANCH, CATEGORIES, CATEGORY_EMOJIS


def save_to_github(filepath: str, content: str, title: str) -> str:
    """
    Create or update a markdown file in the GitHub repo.

    Args:
        filepath: Path within the repo (e.g. "optiplan/2026-03-26_cursor-tips.md")
        content: Markdown content to write
        title: Used in the commit message

    Returns:
        URL of the created/updated file on GitHub.
    """
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    commit_message = f"📝 Add: {title}"

    print(f"📤 Pushing to GitHub: {GITHUB_REPO}/{filepath}...")

    try:
        # Check if file already exists
        existing = repo.get_contents(filepath, ref=GITHUB_BRANCH)
        # Update existing file
        repo.update_file(
            path=filepath,
            message=f"✏️ Update: {title}",
            content=content,
            sha=existing.sha,
            branch=GITHUB_BRANCH,
        )
        print(f"✅ Updated existing file: {filepath}")
    except GithubException as e:
        if e.status == 404:
            # File doesn't exist — create it
            repo.create_file(
                path=filepath,
                message=commit_message,
                content=content,
                branch=GITHUB_BRANCH,
            )
            print(f"✅ Created new file: {filepath}")
        else:
            raise

    file_url = f"https://github.com/{GITHUB_REPO}/blob/{GITHUB_BRANCH}/{filepath}"
    return file_url


def ensure_repo_structure():
    """
    Ensure the repo has the required category folders.
    Creates a .gitkeep in each if missing.
    """
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    for category_key in CATEGORIES:
        gitkeep_path = f"{category_key}/.gitkeep"
        try:
            repo.get_contents(gitkeep_path, ref=GITHUB_BRANCH)
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=gitkeep_path,
                    message=f"📁 Create {category_key}/ folder",
                    content="",
                    branch=GITHUB_BRANCH,
                )
                print(f"  Created folder: {category_key}/")

    # Also ensure _weekly/ and _queue/ exist
    for folder in ["_weekly", "_queue"]:
        gitkeep_path = f"{folder}/.gitkeep"
        try:
            repo.get_contents(gitkeep_path, ref=GITHUB_BRANCH)
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=gitkeep_path,
                    message=f"📁 Create {folder}/ folder",
                    content="",
                    branch=GITHUB_BRANCH,
                )
                print(f"  Created folder: {folder}/")


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    data = {}
    for line in match.group(1).splitlines():
        if ": " in line:
            key, val = line.split(": ", 1)
            # Strip quotes
            val = val.strip().strip('"').strip("'")
            # Parse relevance as int
            if key.strip() == "relevance":
                try:
                    val = int(val)
                except ValueError:
                    val = 3
            data[key.strip()] = val
    return data


def _collect_notes():
    """Read all notes from the repo and return them sorted by date."""
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    notes = []
    for category_key in CATEGORIES:
        try:
            contents = repo.get_contents(category_key, ref=GITHUB_BRANCH)
        except GithubException:
            continue
        for item in contents:
            if item.name.endswith(".md") and item.name != ".gitkeep":
                try:
                    file_content = item.decoded_content.decode("utf-8")
                    fm = _parse_frontmatter(file_content)
                    if fm:
                        fm["_path"] = item.path
                        fm["_category"] = category_key
                        notes.append(fm)
                except Exception:
                    continue

    notes.sort(key=lambda n: n.get("date_processed", ""), reverse=True)
    return notes


def update_index():
    """
    Read all notes from the repo, generate and push an updated README.md index
    and HTML dashboard.
    """
    notes = _collect_notes()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Build category sections
    category_sections = []
    for cat_key, cat_info in CATEGORIES.items():
        cat_notes = [n for n in notes if n.get("_category") == cat_key]
        if not cat_notes:
            continue
        emoji = CATEGORY_EMOJIS.get(cat_key, "📄")
        rows = []
        for n in cat_notes:
            rel = n.get("relevance", 3)
            stars = "⭐" * rel if isinstance(rel, int) else "⭐⭐⭐"
            source = n.get("source", "")
            rows.append(
                f"| {n.get('date_processed', '—')} "
                f"| {n.get('title_he', '—')} "
                f"| {n.get('title_en', '—')} "
                f"| [🔗]({source}) "
                f"| {stars} |"
            )
        section = f"""### {emoji} {cat_info['he']} — {cat_info['en']} ({len(cat_notes)})

| Date | כותרת | Title | Source | Relevance |
|------|-------|-------|--------|-----------|
{chr(10).join(rows)}
"""
        category_sections.append(section)

    # Build full index rows
    all_rows = []
    for n in notes:
        cat_key = n.get("_category", "other")
        cat_he = CATEGORIES.get(cat_key, {}).get("he", "—")
        rel = n.get("relevance", 3)
        stars = "⭐" * rel if isinstance(rel, int) else "⭐⭐⭐"
        source = n.get("source", "")
        all_rows.append(
            f"| {n.get('date_processed', '—')} "
            f"| {cat_he} "
            f"| {n.get('title_he', '—')} "
            f"| {n.get('title_en', '—')} "
            f"| [🔗]({source}) "
            f"| {stars} |"
        )

    # Count categories with notes
    cats_with_notes = len([c for c in CATEGORIES if any(n.get("_category") == c for n in notes)])

    readme = f"""# 🎓 TikTok Knowledge Base

> Auto-generated index of extracted knowledge from TikTok tech videos.
> Last updated: {now}

**Total notes:** {len(notes)} | **Categories:** {cats_with_notes}

---

## 📊 By Category

{chr(10).join(category_sections)}

---

## 📋 Full Index (Newest First)

| Date | Category | כותרת | Title | Source | Relevance |
|------|----------|-------|-------|--------|-----------|
{chr(10).join(all_rows)}

---

*Generated automatically by the TikTok Knowledge Pipeline.*
"""

    # Push README
    save_to_github("README.md", readme, "Update index")

    # Push HTML dashboard
    from .dashboard import generate_dashboard_html
    html = generate_dashboard_html(notes)
    save_to_github("docs/index.html", html, "Update dashboard")
    print(f"Dashboard updated: {len(notes)} notes")
