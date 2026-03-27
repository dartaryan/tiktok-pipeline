"""Generate a TikTok-branded HTML dashboard for the knowledge base."""

import html as html_mod
from datetime import datetime
from .config import CATEGORIES

# Phosphor icon mapping per category
CATEGORY_ICONS = {
    "elon-katzef": "ph ph-brain",
    "shalhevet": "ph ph-flame",
    "taylor-played": "ph ph-game-controller",
    "optiplan": "ph ph-buildings",
    "other": "ph ph-package",
}

# Category accent colors
CATEGORY_COLORS = {
    "elon-katzef": "#25F4EE",
    "shalhevet": "#FF6B35",
    "taylor-played": "#A855F7",
    "optiplan": "#FE2C55",
    "other": "#8A8B91",
}


def _esc(text: str) -> str:
    """HTML-escape text."""
    return html_mod.escape(str(text)) if text else ""


def _build_note_card(note: dict, index: int) -> str:
    """Build HTML for a single rich note card."""
    cat_key = note.get("_category", "other")
    cat_info = CATEGORIES.get(cat_key, {})
    cat_he = cat_info.get("he", cat_key)
    cat_en = cat_info.get("en", cat_key)
    icon_class = CATEGORY_ICONS.get(cat_key, "ph ph-file-text")
    accent = CATEGORY_COLORS.get(cat_key, "#8A8B91")

    title_he = _esc(note.get("title_he", "---"))
    title_en = _esc(note.get("title_en", "---"))
    date = _esc(note.get("date_processed", "---"))
    creator = _esc(note.get("creator", "").lstrip("@"))
    source = _esc(note.get("source", "#"))
    relevance = note.get("relevance", 3)
    rel = int(relevance) if isinstance(relevance, (int, float)) else 3

    stars_html = '<i class="ph-fill ph-star"></i>' * rel + '<i class="ph ph-star"></i>' * (5 - rel)

    # Tags
    tags = note.get("tags", "")
    tags_html = ""
    if tags and isinstance(tags, str):
        tag_list = [t.strip().strip('"').strip("'") for t in tags.strip("[]").split(",") if t.strip()]
        tags_html = "".join(f'<span class="tag">{_esc(t)}</span>' for t in tag_list[:5])

    # Summary
    summary = _esc(note.get("_summary", ""))
    summary_html = f'<p class="card-summary">{summary}</p>' if summary else ""

    # Key insights
    insights = note.get("_insights", [])
    insights_html = ""
    if insights:
        items = "".join(f"<li>{_esc(i)}</li>" for i in insights[:4])
        insights_html = f"""
        <div class="card-section">
          <div class="card-section-title"><i class="ph ph-lightbulb"></i> Insights</div>
          <ul class="card-list">{items}</ul>
        </div>"""

    # Tools
    tools = note.get("_tools", [])
    tools_html = ""
    if tools:
        tool_items = "".join(f"<li>{_esc(t.strip('| '))}</li>" for t in tools[:3])
        tools_html = f"""
        <div class="card-section">
          <div class="card-section-title"><i class="ph ph-wrench"></i> Tools</div>
          <ul class="card-list">{tool_items}</ul>
        </div>"""

    # Action items
    actions = note.get("_actions", [])
    actions_html = ""
    if actions:
        action_items = "".join(f'<li><i class="ph ph-check-square"></i> {_esc(a)}</li>' for a in actions[:3])
        actions_html = f"""
        <div class="card-section">
          <div class="card-section-title"><i class="ph ph-list-checks"></i> Action Items</div>
          <ul class="card-list actions">{action_items}</ul>
        </div>"""

    # Verification
    verification = note.get("_verification", [])
    verif_html = ""
    if verification:
        v_items = "".join(f"<li>{_esc(v)}</li>" for v in verification[:2])
        verif_html = f"""
        <div class="card-section verification">
          <div class="card-section-title"><i class="ph ph-warning"></i> Verification</div>
          <ul class="card-list">{v_items}</ul>
        </div>"""

    has_details = any([insights, tools, actions, verification])
    expand_btn = f'<button class="expand-btn" onclick="toggleCard(this)"><i class="ph ph-caret-down"></i></button>' if has_details else ""

    return f"""
    <article class="card" data-category="{cat_key}" style="--accent:{accent}">
      <div class="card-glow"></div>
      <div class="card-header">
        <div class="card-icon"><i class="{icon_class}"></i></div>
        <div class="card-meta">
          <span class="card-category">{cat_he} &middot; {cat_en}</span>
          <span class="card-date"><i class="ph ph-calendar-blank"></i> {date}{f' &middot; @{creator}' if creator else ''}</span>
        </div>
        <div class="card-relevance">{stars_html}</div>
      </div>
      <h3 class="card-title-he">{title_he}</h3>
      <p class="card-title-en">{title_en}</p>
      {summary_html}
      <div class="card-details">
        {insights_html}
        {tools_html}
        {actions_html}
        {verif_html}
      </div>
      <div class="card-footer">
        <div class="card-tags">{tags_html}</div>
        {expand_btn}
        <a href="{source}" target="_blank" rel="noopener" class="card-source">
          <i class="ph ph-arrow-square-out"></i> Source
        </a>
      </div>
    </article>"""


def _build_filters(notes: list) -> str:
    """Build the category filter pills."""
    buttons = ['<button class="filter-btn active" data-filter="all"><i class="ph ph-squares-four"></i> All</button>']
    for cat_key, cat_info in CATEGORIES.items():
        count = sum(1 for n in notes if n.get("_category") == cat_key)
        if count == 0:
            continue
        icon = CATEGORY_ICONS.get(cat_key, "ph ph-file-text")
        accent = CATEGORY_COLORS.get(cat_key, "#8A8B91")
        buttons.append(
            f'<button class="filter-btn" data-filter="{cat_key}" style="--btn-accent:{accent}">'
            f'<i class="{icon}"></i> {cat_info["en"]} <span class="count">{count}</span>'
            f'</button>'
        )
    return "\n".join(buttons)


def generate_dashboard_html(notes: list) -> str:
    """Generate the full HTML dashboard page."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(notes)
    cats_with_notes = len(set(n.get("_category") for n in notes))

    notes_sorted = sorted(notes, key=lambda n: n.get("date_processed", ""), reverse=True)

    cards_html = "\n".join(_build_note_card(n, i) for i, n in enumerate(notes_sorted))
    filters_html = _build_filters(notes_sorted)

    avg_rel = sum(
        int(n.get("relevance", 3)) if isinstance(n.get("relevance", 3), (int, float)) else 3
        for n in notes
    ) / max(total, 1)

    # SVG favicon (TikTok-inspired music note)
    favicon_svg = "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' rx='8' fill='%23000'/><text x='16' y='24' text-anchor='middle' font-size='22' fill='%2325F4EE'>K</text></svg>"

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TikTok Knowledge Base</title>
  <link rel="icon" href="{favicon_svg}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Nunito:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #010102;
      --bg-elevated: #0d0d14;
      --surface: rgba(255,255,255,0.05);
      --surface-hover: rgba(255,255,255,0.09);
      --pink: #FE2C55;
      --cyan: #25F4EE;
      --purple: #A855F7;
      --white: #EDEDEF;
      --muted: #9ca3af;
      --dim: #4b5563;
      --border: rgba(255,255,255,0.08);
      --radius: 20px;
      --ease: cubic-bezier(0.16,1,0.3,1);
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: 'Nunito', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--white);
      min-height: 100vh;
      direction: rtl;
      overflow-x: hidden;
    }}

    h1, h2, h3, .stat-value, .logo-badge span {{
      font-family: 'Fredoka', 'Nunito', sans-serif;
    }}

    /* === Ambient blobs === */
    .ambient {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      overflow: hidden;
    }}
    .blob {{
      position: absolute;
      border-radius: 50%;
      filter: blur(100px);
      opacity: 0.15;
      animation: drift 25s ease-in-out infinite alternate;
    }}
    .blob-pink {{
      width: 600px; height: 600px;
      background: var(--pink);
      top: -15%; right: -10%;
    }}
    .blob-cyan {{
      width: 500px; height: 500px;
      background: var(--cyan);
      bottom: 5%; left: -10%;
      animation-delay: -12s;
      animation-direction: alternate-reverse;
    }}
    .blob-purple {{
      width: 350px; height: 350px;
      background: var(--purple);
      top: 40%; left: 50%;
      animation-delay: -6s;
      opacity: 0.08;
    }}
    @keyframes drift {{
      0% {{ transform: translate(0, 0) scale(1) rotate(0deg); }}
      100% {{ transform: translate(50px, -40px) scale(1.15) rotate(5deg); }}
    }}

    /* === Floating particles === */
    .particles {{
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      overflow: hidden;
    }}
    .particle {{
      position: absolute;
      width: 4px; height: 4px;
      border-radius: 50%;
      opacity: 0;
      animation: floatUp linear infinite;
    }}
    @keyframes floatUp {{
      0% {{ opacity: 0; transform: translateY(100vh) scale(0); }}
      10% {{ opacity: 0.6; }}
      90% {{ opacity: 0.6; }}
      100% {{ opacity: 0; transform: translateY(-10vh) scale(1); }}
    }}

    /* === Layout === */
    .page {{ position: relative; z-index: 1; }}

    /* === Hero === */
    .hero {{
      padding: 80px 24px 40px;
      text-align: center;
      animation: heroIn 0.8s var(--ease) backwards;
    }}
    @keyframes heroIn {{
      from {{ opacity: 0; transform: translateY(-30px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .logo-badge {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      padding: 10px 24px 10px 14px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 100px;
      margin-bottom: 24px;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      position: relative;
      overflow: hidden;
      animation: heroIn 0.8s var(--ease) 0.1s backwards;
    }}
    .logo-badge::before {{
      content: '';
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
      animation: shimmer 3s ease-in-out infinite;
    }}
    @keyframes shimmer {{
      0%,100% {{ transform: translateX(-100%); }}
      50% {{ transform: translateX(100%); }}
    }}

    .logo-badge .badge-icon {{
      width: 32px; height: 32px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--cyan), var(--pink));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      color: #fff;
      animation: iconPulse 3s ease-in-out infinite;
    }}
    @keyframes iconPulse {{
      0%,100% {{ box-shadow: 0 0 0 0 rgba(37,244,238,0.3); }}
      50% {{ box-shadow: 0 0 0 8px rgba(37,244,238,0); }}
    }}

    .logo-badge span {{
      font-size: 14px;
      font-weight: 600;
      color: var(--muted);
      letter-spacing: 1.5px;
      text-transform: uppercase;
    }}

    .hero h1 {{
      font-size: clamp(40px, 7vw, 72px);
      font-weight: 700;
      letter-spacing: -1.5px;
      line-height: 1.1;
      background: linear-gradient(135deg, var(--white) 0%, var(--cyan) 50%, var(--pink) 100%);
      background-size: 200% 200%;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
      animation: gradientShift 6s ease-in-out infinite, heroIn 0.8s var(--ease) 0.2s backwards;
    }}
    @keyframes gradientShift {{
      0%,100% {{ background-position: 0% 50%; }}
      50% {{ background-position: 100% 50%; }}
    }}

    .hero-sub {{
      color: var(--muted);
      font-size: 18px;
      margin-top: 16px;
      font-weight: 500;
      animation: heroIn 0.8s var(--ease) 0.3s backwards;
    }}

    /* === Stats === */
    .stats {{
      display: flex;
      justify-content: center;
      gap: 20px;
      padding: 24px 24px 32px;
      flex-wrap: wrap;
      animation: heroIn 0.8s var(--ease) 0.4s backwards;
    }}

    .stat {{
      text-align: center;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 20px 32px;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      transition: transform 0.3s var(--ease), border-color 0.3s var(--ease), box-shadow 0.3s var(--ease);
      cursor: default;
    }}
    .stat:hover {{
      transform: translateY(-4px);
      border-color: rgba(37,244,238,0.2);
      box-shadow: 0 8px 32px rgba(37,244,238,0.08);
    }}

    .stat-icon {{
      font-size: 24px;
      margin-bottom: 8px;
      display: block;
    }}
    .stat:nth-child(1) .stat-icon {{ color: var(--pink); }}
    .stat:nth-child(2) .stat-icon {{ color: var(--cyan); }}
    .stat:nth-child(3) .stat-icon {{ color: var(--purple); }}

    .stat-value {{
      font-size: 36px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--pink), var(--cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .stat-label {{
      font-size: 12px;
      color: var(--dim);
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-top: 4px;
      font-weight: 600;
    }}

    /* === Search === */
    .search-wrap {{
      max-width: 560px;
      margin: 0 auto 16px;
      padding: 0 24px;
      position: relative;
      animation: heroIn 0.8s var(--ease) 0.5s backwards;
    }}

    .search-input {{
      width: 100%;
      padding: 16px 24px 16px 52px;
      border-radius: 100px;
      border: 1px solid var(--border);
      background: var(--surface);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      color: var(--white);
      font-family: inherit;
      font-size: 16px;
      outline: none;
      transition: border-color 0.3s var(--ease), box-shadow 0.3s var(--ease), background 0.3s var(--ease);
    }}
    .search-input::placeholder {{ color: var(--dim); font-size: 15px; }}
    .search-input:focus {{
      border-color: rgba(37,244,238,0.4);
      box-shadow: 0 0 0 4px rgba(37,244,238,0.1), 0 4px 24px rgba(37,244,238,0.06);
      background: rgba(255,255,255,0.07);
    }}

    .search-icon {{
      position: absolute;
      right: 44px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: 20px;
      pointer-events: none;
      transition: color 0.3s;
    }}
    .search-input:focus ~ .search-icon {{ color: var(--cyan); }}

    /* === Filters === */
    .filters {{
      display: flex;
      gap: 10px;
      padding: 16px 24px 24px;
      overflow-x: auto;
      scrollbar-width: none;
      justify-content: center;
      flex-wrap: wrap;
      animation: heroIn 0.8s var(--ease) 0.55s backwards;
    }}
    .filters::-webkit-scrollbar {{ display: none; }}

    .filter-btn {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 22px;
      border: 1px solid var(--border);
      border-radius: 100px;
      background: transparent;
      color: var(--muted);
      font-family: 'Fredoka', sans-serif;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.3s var(--ease);
      white-space: nowrap;
    }}
    .filter-btn:hover {{
      border-color: var(--dim);
      color: var(--white);
      background: var(--surface);
      transform: translateY(-2px);
    }}
    .filter-btn:active {{
      transform: translateY(0) scale(0.96);
    }}
    .filter-btn.active {{
      background: linear-gradient(135deg, var(--pink), var(--cyan));
      color: #fff;
      border-color: transparent;
      font-weight: 600;
      box-shadow: 0 4px 20px rgba(254,44,85,0.25);
    }}
    .filter-btn .count {{
      font-size: 12px;
      opacity: 0.7;
      background: rgba(255,255,255,0.15);
      padding: 1px 8px;
      border-radius: 100px;
    }}

    /* === Divider === */
    .divider {{
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--pink) 30%, var(--cyan) 70%, transparent);
      margin: 0 40px;
      opacity: 0.3;
    }}

    /* === Cards === */
    .cards-container {{
      max-width: 1320px;
      margin: 0 auto;
      padding: 36px 24px;
    }}
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
      gap: 24px;
    }}

    .card {{
      position: relative;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 28px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      transition: transform 0.4s var(--ease), border-color 0.4s var(--ease), box-shadow 0.4s var(--ease);
      overflow: hidden;
      opacity: 0;
      transform: translateY(40px);
    }}
    .card.revealed {{
      opacity: 1;
      transform: translateY(0);
      transition: opacity 0.6s var(--ease), transform 0.6s var(--ease), border-color 0.4s var(--ease), box-shadow 0.4s var(--ease);
    }}
    .card:hover {{
      transform: translateY(-6px) scale(1.01);
      border-color: color-mix(in srgb, var(--accent) 40%, transparent);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5),
                  0 0 0 1px color-mix(in srgb, var(--accent) 20%, transparent),
                  0 0 40px color-mix(in srgb, var(--accent) 8%, transparent);
    }}

    .card-glow {{
      position: absolute;
      top: -20px; right: -20px;
      width: 160px; height: 160px;
      background: radial-gradient(circle, color-mix(in srgb, var(--accent) 15%, transparent), transparent 70%);
      pointer-events: none;
      transition: opacity 0.4s;
      opacity: 0.5;
    }}
    .card:hover .card-glow {{ opacity: 1; }}

    .card-header {{
      display: flex;
      align-items: center;
      gap: 14px;
    }}

    .card-icon {{
      width: 48px; height: 48px;
      border-radius: 14px;
      background: linear-gradient(135deg, color-mix(in srgb, var(--accent) 20%, transparent), color-mix(in srgb, var(--accent) 8%, transparent));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 24px;
      color: var(--accent);
      flex-shrink: 0;
      transition: transform 0.3s var(--ease), box-shadow 0.3s var(--ease);
    }}
    .card:hover .card-icon {{
      transform: scale(1.1) rotate(-5deg);
      box-shadow: 0 0 20px color-mix(in srgb, var(--accent) 20%, transparent);
    }}

    .card-meta {{
      flex: 1;
      min-width: 0;
    }}
    .card-category {{
      font-size: 12px;
      font-weight: 600;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 1px;
      font-family: 'Fredoka', sans-serif;
    }}
    .card-date {{
      font-size: 12px;
      color: var(--dim);
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 2px;
    }}

    .card-relevance {{
      display: flex;
      gap: 3px;
      font-size: 15px;
      flex-shrink: 0;
    }}
    .card-relevance .ph-fill {{ color: #FBBF24; }}
    .card-relevance .ph {{ color: var(--dim); }}

    .card-title-he {{
      font-size: 22px;
      font-weight: 600;
      line-height: 1.5;
      color: var(--white);
    }}

    .card-title-en {{
      font-size: 15px;
      color: var(--muted);
      line-height: 1.5;
    }}

    .card-summary {{
      font-size: 15px;
      line-height: 1.8;
      color: var(--muted);
      border-inline-start: 3px solid color-mix(in srgb, var(--accent) 50%, transparent);
      padding-inline-start: 14px;
      background: color-mix(in srgb, var(--accent) 3%, transparent);
      border-radius: 0 8px 8px 0;
      padding: 10px 14px;
    }}

    /* === Card sections === */
    .card-details {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow: hidden;
      max-height: 0;
      opacity: 0;
      transition: max-height 0.5s var(--ease), opacity 0.4s var(--ease), margin 0.4s var(--ease);
      margin-top: -8px;
    }}
    .card-details.open {{
      max-height: 800px;
      opacity: 1;
      margin-top: 0;
    }}

    .card-section {{
      background: var(--surface);
      border-radius: 12px;
      padding: 14px 16px;
    }}
    .card-section.verification {{
      border: 1px solid rgba(251,191,36,0.15);
      background: rgba(251,191,36,0.04);
    }}

    .card-section-title {{
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: var(--muted);
      margin-bottom: 10px;
      display: flex;
      align-items: center;
      gap: 8px;
      font-family: 'Fredoka', sans-serif;
    }}
    .card-section-title i {{ font-size: 16px; color: var(--accent); }}
    .card-section.verification .card-section-title i {{ color: #FBBF24; }}

    .card-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .card-list li {{
      font-size: 14px;
      line-height: 1.7;
      color: var(--muted);
      padding-inline-start: 14px;
      position: relative;
    }}
    .card-list li::before {{
      content: '';
      position: absolute;
      right: 0;
      top: 10px;
      width: 5px; height: 5px;
      border-radius: 50%;
      background: var(--accent);
      opacity: 0.5;
    }}
    .card-list.actions li {{
      display: flex;
      align-items: flex-start;
      gap: 8px;
      padding-inline-start: 0;
    }}
    .card-list.actions li::before {{ display: none; }}
    .card-list.actions li i {{ color: var(--accent); margin-top: 3px; flex-shrink: 0; font-size: 16px; }}

    /* === Expand === */
    .expand-btn {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 100px;
      width: 36px; height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      font-size: 18px;
      cursor: pointer;
      transition: all 0.3s var(--ease);
      flex-shrink: 0;
    }}
    .expand-btn:hover {{
      background: var(--surface-hover);
      color: var(--white);
      border-color: var(--dim);
      transform: scale(1.1);
    }}
    .expand-btn.open {{ transform: rotate(180deg); }}
    .expand-btn.open:hover {{ transform: rotate(180deg) scale(1.1); }}

    /* === Card Footer === */
    .card-footer {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin-top: auto;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      flex-wrap: wrap;
    }}

    .card-tags {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      flex: 1;
    }}
    .tag {{
      padding: 4px 12px;
      border-radius: 100px;
      font-size: 12px;
      background: var(--surface);
      color: var(--dim);
      border: 1px solid var(--border);
      transition: all 0.3s var(--ease);
      font-weight: 500;
    }}
    .card:hover .tag {{
      color: var(--muted);
      border-color: color-mix(in srgb, var(--accent) 20%, transparent);
    }}

    .card-source {{
      color: var(--cyan);
      font-size: 13px;
      font-weight: 600;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.3s var(--ease);
      padding: 6px 14px;
      border-radius: 100px;
      background: rgba(37,244,238,0.08);
    }}
    .card-source:hover {{
      background: rgba(37,244,238,0.15);
      transform: translateX(-4px);
    }}
    .card-source i {{ transition: transform 0.3s var(--ease); }}
    .card-source:hover i {{ transform: translate(-2px, -2px); }}

    /* === Empty === */
    .empty {{
      text-align: center;
      padding: 100px 24px;
      color: var(--dim);
    }}
    .empty i {{ font-size: 56px; display: block; margin-bottom: 16px; opacity: 0.5; }}
    .empty p {{ font-size: 18px; font-family: 'Fredoka', sans-serif; }}

    /* === Page Footer === */
    footer {{
      text-align: center;
      padding: 56px 24px;
      color: var(--dim);
      font-size: 14px;
    }}
    footer a {{
      color: var(--muted);
      text-decoration: none;
      transition: color 0.3s;
      font-weight: 600;
    }}
    footer a:hover {{ color: var(--cyan); }}
    footer .footer-heart {{
      display: inline-block;
      color: var(--pink);
      animation: heartbeat 2s ease-in-out infinite;
    }}
    @keyframes heartbeat {{
      0%,100% {{ transform: scale(1); }}
      50% {{ transform: scale(1.2); }}
    }}

    /* === Scroll to top === */
    .scroll-top {{
      position: fixed;
      bottom: 28px;
      left: 28px;
      width: 48px; height: 48px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--pink), var(--cyan));
      border: none;
      color: #fff;
      font-size: 22px;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      opacity: 0;
      transform: translateY(20px);
      transition: all 0.4s var(--ease);
      z-index: 100;
      box-shadow: 0 4px 20px rgba(254,44,85,0.3);
    }}
    .scroll-top.visible {{
      opacity: 1;
      transform: translateY(0);
    }}
    .scroll-top:hover {{
      transform: translateY(-4px) scale(1.1);
      box-shadow: 0 8px 30px rgba(254,44,85,0.4);
    }}

    /* === Reduced motion === */
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
      }}
      .card {{ opacity: 1; transform: none; }}
      .card.revealed {{ transition: none; }}
      .particle {{ display: none; }}
    }}

    /* === Responsive === */
    @media (max-width: 640px) {{
      .cards-grid {{ grid-template-columns: 1fr; }}
      .stats {{ gap: 12px; }}
      .stat {{ padding: 14px 20px; }}
      .stat-value {{ font-size: 28px; }}
      .hero {{ padding: 48px 16px 28px; }}
      .hero h1 {{ letter-spacing: -0.5px; }}
      .card {{ padding: 20px; }}
      .card-icon {{ width: 42px; height: 42px; font-size: 20px; }}
      .card-title-he {{ font-size: 19px; }}
    }}
    @media (max-width: 420px) {{
      .stats {{ flex-direction: column; align-items: center; }}
      .stat {{ width: 100%; max-width: 240px; }}
    }}
  </style>
</head>
<body>

  <!-- Ambient background -->
  <div class="ambient">
    <div class="blob blob-pink"></div>
    <div class="blob blob-cyan"></div>
    <div class="blob blob-purple"></div>
  </div>

  <!-- Floating particles -->
  <div class="particles" id="particles"></div>

  <div class="page">
    <!-- Hero -->
    <section class="hero">
      <div class="logo-badge">
        <div class="badge-icon"><i class="ph ph-music-notes-simple"></i></div>
        <span>Knowledge Base</span>
      </div>
      <h1>TikTok Knowledge</h1>
      <p class="hero-sub"><i class="ph ph-sparkle"></i> AI-extracted insights from tech TikTok <i class="ph ph-dot-outline"></i> auto-classified <i class="ph ph-dot-outline"></i> translated to Hebrew</p>
    </section>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <i class="ph ph-note-pencil stat-icon"></i>
        <div class="stat-value" data-target="{total}">0</div>
        <div class="stat-label">Notes</div>
      </div>
      <div class="stat">
        <i class="ph ph-folders stat-icon"></i>
        <div class="stat-value" data-target="{cats_with_notes}">0</div>
        <div class="stat-label">Categories</div>
      </div>
      <div class="stat">
        <i class="ph ph-star stat-icon"></i>
        <div class="stat-value" data-target="{avg_rel:.1f}" data-decimal="true">0</div>
        <div class="stat-label">Avg Relevance</div>
      </div>
    </div>

    <!-- Search -->
    <div class="search-wrap">
      <input type="text" class="search-input" placeholder="Search notes..." id="searchInput" aria-label="Search notes">
      <i class="ph ph-magnifying-glass search-icon"></i>
    </div>

    <!-- Filters -->
    <div class="filters" id="filters">
      {filters_html}
    </div>

    <div class="divider"></div>

    <!-- Cards -->
    <div class="cards-container">
      <div class="cards-grid" id="cardsGrid">
        {cards_html}
      </div>
      <div class="empty" id="emptyState" style="display:none">
        <i class="ph ph-magnifying-glass"></i>
        <p>No notes match your search</p>
      </div>
    </div>

    <!-- Footer -->
    <footer>
      <p>Last updated: {now}</p>
      <p style="margin-top:8px">
        Built with <span class="footer-heart"><i class="ph-fill ph-heart"></i></span>
        using <a href="https://github.com/dartaryan/tiktok-pipeline">TikTok Knowledge Pipeline</a>
      </p>
    </footer>
  </div>

  <!-- Scroll to top -->
  <button class="scroll-top" id="scrollTop" aria-label="Scroll to top">
    <i class="ph ph-arrow-up"></i>
  </button>

  <script>
    /* === Particles === */
    (function createParticles() {{
      const container = document.getElementById('particles');
      const colors = ['#FE2C55', '#25F4EE', '#A855F7', '#FBBF24'];
      for (let i = 0; i < 20; i++) {{
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.width = p.style.height = (2 + Math.random() * 4) + 'px';
        p.style.background = colors[Math.floor(Math.random() * colors.length)];
        p.style.animationDuration = (12 + Math.random() * 18) + 's';
        p.style.animationDelay = (Math.random() * 15) + 's';
        container.appendChild(p);
      }}
    }})();

    /* === Counter animation === */
    function animateCounters() {{
      document.querySelectorAll('.stat-value[data-target]').forEach(el => {{
        const target = parseFloat(el.dataset.target);
        const isDecimal = el.dataset.decimal === 'true';
        const duration = 1500;
        const start = performance.now();
        function tick(now) {{
          const progress = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          const current = target * eased;
          el.textContent = isDecimal ? current.toFixed(1) : Math.round(current);
          if (progress < 1) requestAnimationFrame(tick);
        }}
        requestAnimationFrame(tick);
      }});
    }}
    animateCounters();

    /* === Scroll reveal === */
    const revealObserver = new IntersectionObserver((entries) => {{
      entries.forEach((entry, i) => {{
        if (entry.isIntersecting) {{
          const card = entry.target;
          const idx = Array.from(card.parentElement.children).indexOf(card);
          setTimeout(() => card.classList.add('revealed'), idx * 80);
          revealObserver.unobserve(card);
        }}
      }});
    }}, {{ threshold: 0.08, rootMargin: '0px 0px -40px 0px' }});

    document.querySelectorAll('.card').forEach(card => revealObserver.observe(card));

    /* === Filters & search === */
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.card');
    const emptyState = document.getElementById('emptyState');
    const searchInput = document.getElementById('searchInput');
    let activeFilter = 'all';

    function applyFilters() {{
      const q = searchInput.value.toLowerCase().trim();
      let vis = 0;
      cards.forEach(c => {{
        const catOk = activeFilter === 'all' || c.dataset.category === activeFilter;
        const searchOk = !q || c.textContent.toLowerCase().includes(q);
        const show = catOk && searchOk;
        c.style.display = show ? '' : 'none';
        if (show) {{
          vis++;
          if (!c.classList.contains('revealed')) c.classList.add('revealed');
        }}
      }});
      emptyState.style.display = vis === 0 ? '' : 'none';
    }}

    filterBtns.forEach(btn => {{
      btn.addEventListener('click', () => {{
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        applyFilters();
      }});
    }});

    searchInput.addEventListener('input', applyFilters);

    /* === Card expand/collapse === */
    function toggleCard(btn) {{
      const card = btn.closest('.card');
      const details = card.querySelector('.card-details');
      const isOpen = details.classList.contains('open');
      details.classList.toggle('open', !isOpen);
      btn.classList.toggle('open', !isOpen);
    }}

    /* === Scroll to top === */
    const scrollBtn = document.getElementById('scrollTop');
    window.addEventListener('scroll', () => {{
      scrollBtn.classList.toggle('visible', window.scrollY > 400);
    }});
    scrollBtn.addEventListener('click', () => {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  </script>
</body>
</html>"""
