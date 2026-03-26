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

    delay = min(index * 0.04, 0.4)

    return f"""
    <article class="card" data-category="{cat_key}" style="--accent:{accent};animation-delay:{delay}s">
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
      <div class="card-details" style="display:none">
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
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/regular/style.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.1/src/fill/style.css" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #010102;
      --bg-elevated: #0a0a0f;
      --surface: rgba(255,255,255,0.04);
      --surface-hover: rgba(255,255,255,0.07);
      --pink: #FE2C55;
      --cyan: #25F4EE;
      --white: #EDEDEF;
      --muted: #8A8B91;
      --dim: #3A3B44;
      --border: rgba(255,255,255,0.07);
      --radius: 16px;
      --ease: cubic-bezier(0.16,1,0.3,1);
    }}

    body {{
      font-family: 'Inter', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--white);
      min-height: 100vh;
      direction: rtl;
      overflow-x: hidden;
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
      filter: blur(80px);
      opacity: 0.12;
      animation: drift 20s ease-in-out infinite alternate;
    }}
    .blob-pink {{
      width: 500px; height: 500px;
      background: var(--pink);
      top: -10%; right: -10%;
    }}
    .blob-cyan {{
      width: 400px; height: 400px;
      background: var(--cyan);
      bottom: 10%; left: -8%;
      animation-delay: -10s;
      animation-direction: alternate-reverse;
    }}
    @keyframes drift {{
      0% {{ transform: translate(0, 0) scale(1); }}
      100% {{ transform: translate(40px, -30px) scale(1.1); }}
    }}

    /* === Layout === */
    .page {{ position: relative; z-index: 1; }}

    /* === Hero === */
    .hero {{
      padding: 64px 24px 32px;
      text-align: center;
    }}

    .logo-badge {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 20px 8px 12px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 100px;
      margin-bottom: 20px;
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
    }}

    .logo-badge i {{
      font-size: 20px;
      background: linear-gradient(135deg, var(--cyan), var(--pink));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .logo-badge span {{
      font-size: 13px;
      font-weight: 600;
      color: var(--muted);
      letter-spacing: 1px;
      text-transform: uppercase;
    }}

    .hero h1 {{
      font-size: clamp(32px, 6vw, 56px);
      font-weight: 700;
      letter-spacing: -1px;
      line-height: 1.1;
      background: linear-gradient(135deg, var(--white) 0%, var(--muted) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .hero-sub {{
      color: var(--muted);
      font-size: 16px;
      margin-top: 12px;
    }}

    /* === Stats === */
    .stats {{
      display: flex;
      justify-content: center;
      gap: 48px;
      padding: 20px 24px 28px;
    }}

    .stat {{ text-align: center; }}

    .stat-value {{
      font-size: 32px;
      font-weight: 700;
      background: linear-gradient(135deg, var(--pink), var(--cyan));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }}

    .stat-label {{
      font-size: 11px;
      color: var(--dim);
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-top: 2px;
    }}

    /* === Search === */
    .search-wrap {{
      max-width: 520px;
      margin: 0 auto 12px;
      padding: 0 24px;
      position: relative;
    }}

    .search-input {{
      width: 100%;
      padding: 14px 20px 14px 48px;
      border-radius: 100px;
      border: 1px solid var(--border);
      background: var(--surface);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      color: var(--white);
      font-family: inherit;
      font-size: 14px;
      outline: none;
      transition: border-color 0.3s var(--ease), box-shadow 0.3s var(--ease);
    }}
    .search-input::placeholder {{ color: var(--dim); }}
    .search-input:focus {{
      border-color: rgba(37,244,238,0.3);
      box-shadow: 0 0 0 3px rgba(37,244,238,0.08);
    }}

    .search-icon {{
      position: absolute;
      right: 42px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--muted);
      font-size: 18px;
      pointer-events: none;
    }}

    /* === Filters === */
    .filters {{
      display: flex;
      gap: 8px;
      padding: 12px 24px 20px;
      overflow-x: auto;
      scrollbar-width: none;
      justify-content: center;
      flex-wrap: wrap;
    }}
    .filters::-webkit-scrollbar {{ display: none; }}

    .filter-btn {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 8px 18px;
      border: 1px solid var(--border);
      border-radius: 100px;
      background: transparent;
      color: var(--muted);
      font-family: inherit;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.25s var(--ease);
      white-space: nowrap;
    }}
    .filter-btn:hover {{
      border-color: var(--dim);
      color: var(--white);
      background: var(--surface);
    }}
    .filter-btn.active {{
      background: var(--white);
      color: #010102;
      border-color: var(--white);
      font-weight: 600;
    }}
    .filter-btn .count {{
      font-size: 11px;
      opacity: 0.6;
    }}

    /* === Divider === */
    .divider {{
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--dim) 50%, transparent);
      margin: 0 40px;
    }}

    /* === Cards === */
    .cards-container {{
      max-width: 1280px;
      margin: 0 auto;
      padding: 28px 24px;
    }}
    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
      gap: 16px;
    }}

    .card {{
      position: relative;
      background: var(--bg-elevated);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: transform 0.3s var(--ease), border-color 0.3s var(--ease), box-shadow 0.3s var(--ease);
      animation: fadeUp 0.5s var(--ease) backwards;
      overflow: hidden;
    }}
    .card:hover {{
      transform: translateY(-3px);
      border-color: color-mix(in srgb, var(--accent) 30%, transparent);
      box-shadow: 0 12px 40px rgba(0,0,0,0.4), 0 0 0 1px color-mix(in srgb, var(--accent) 15%, transparent);
    }}

    .card-glow {{
      position: absolute;
      top: 0; right: 0;
      width: 120px; height: 120px;
      background: radial-gradient(circle, color-mix(in srgb, var(--accent) 12%, transparent), transparent 70%);
      pointer-events: none;
    }}

    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(20px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card-header {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .card-icon {{
      width: 40px; height: 40px;
      border-radius: 10px;
      background: color-mix(in srgb, var(--accent) 12%, transparent);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      color: var(--accent);
      flex-shrink: 0;
    }}

    .card-meta {{
      flex: 1;
      min-width: 0;
    }}
    .card-category {{
      font-size: 11px;
      font-weight: 600;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.8px;
    }}
    .card-date {{
      font-size: 11px;
      color: var(--dim);
      display: flex;
      align-items: center;
      gap: 4px;
      margin-top: 1px;
    }}

    .card-relevance {{
      display: flex;
      gap: 2px;
      font-size: 13px;
      flex-shrink: 0;
    }}
    .card-relevance .ph-fill {{ color: #FBBF24; }}
    .card-relevance .ph {{ color: var(--dim); }}

    .card-title-he {{
      font-size: 18px;
      font-weight: 600;
      line-height: 1.5;
      color: var(--white);
    }}

    .card-title-en {{
      font-size: 13px;
      color: var(--muted);
      line-height: 1.4;
    }}

    .card-summary {{
      font-size: 14px;
      line-height: 1.7;
      color: var(--muted);
      border-inline-start: 2px solid color-mix(in srgb, var(--accent) 40%, transparent);
      padding-inline-start: 12px;
    }}

    /* === Card sections === */
    .card-details {{ display: flex; flex-direction: column; gap: 12px; }}

    .card-section {{
      background: var(--surface);
      border-radius: 10px;
      padding: 12px 14px;
    }}
    .card-section.verification {{
      border: 1px solid rgba(251,191,36,0.15);
      background: rgba(251,191,36,0.04);
    }}

    .card-section-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: var(--muted);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .card-section-title i {{ font-size: 14px; color: var(--accent); }}
    .card-section.verification .card-section-title i {{ color: #FBBF24; }}

    .card-list {{
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }}
    .card-list li {{
      font-size: 13px;
      line-height: 1.6;
      color: var(--muted);
      padding-inline-start: 12px;
      position: relative;
    }}
    .card-list li::before {{
      content: '';
      position: absolute;
      right: 0;
      top: 9px;
      width: 4px; height: 4px;
      border-radius: 50%;
      background: var(--dim);
    }}
    .card-list.actions li {{
      display: flex;
      align-items: flex-start;
      gap: 6px;
      padding-inline-start: 0;
    }}
    .card-list.actions li::before {{ display: none; }}
    .card-list.actions li i {{ color: var(--accent); margin-top: 3px; flex-shrink: 0; }}

    /* === Expand === */
    .expand-btn {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 100px;
      width: 32px; height: 32px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      font-size: 16px;
      cursor: pointer;
      transition: all 0.25s var(--ease);
      flex-shrink: 0;
    }}
    .expand-btn:hover {{ background: var(--surface-hover); color: var(--white); }}
    .expand-btn.open {{ transform: rotate(180deg); }}

    /* === Footer === */
    .card-footer {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: auto;
      padding-top: 14px;
      border-top: 1px solid var(--border);
      flex-wrap: wrap;
    }}

    .card-tags {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      flex: 1;
    }}
    .tag {{
      padding: 3px 10px;
      border-radius: 100px;
      font-size: 11px;
      background: var(--surface);
      color: var(--dim);
      border: 1px solid var(--border);
      transition: color 0.2s;
    }}
    .card:hover .tag {{ color: var(--muted); }}

    .card-source {{
      color: var(--cyan);
      font-size: 12px;
      font-weight: 500;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: opacity 0.2s;
    }}
    .card-source:hover {{ opacity: 0.7; }}

    /* === Empty === */
    .empty {{
      text-align: center;
      padding: 80px 24px;
      color: var(--dim);
    }}
    .empty i {{ font-size: 48px; display: block; margin-bottom: 12px; }}

    /* === Footer === */
    footer {{
      text-align: center;
      padding: 48px 24px;
      color: var(--dim);
      font-size: 12px;
    }}
    footer a {{ color: var(--muted); text-decoration: none; transition: color 0.2s; }}
    footer a:hover {{ color: var(--white); }}

    /* === Responsive === */
    @media (max-width: 640px) {{
      .cards-grid {{ grid-template-columns: 1fr; }}
      .stats {{ gap: 28px; }}
      .hero {{ padding: 40px 16px 24px; }}
      .card {{ padding: 18px; }}
    }}
  </style>
</head>
<body>

  <!-- Ambient background -->
  <div class="ambient">
    <div class="blob blob-pink"></div>
    <div class="blob blob-cyan"></div>
  </div>

  <div class="page">
    <!-- Hero -->
    <section class="hero">
      <div class="logo-badge">
        <i class="ph ph-video"></i>
        <span>Knowledge Base</span>
      </div>
      <h1>TikTok Knowledge</h1>
      <p class="hero-sub">AI-extracted insights from tech TikTok &middot; auto-classified &middot; translated to Hebrew</p>
    </section>

    <!-- Stats -->
    <div class="stats">
      <div class="stat">
        <div class="stat-value">{total}</div>
        <div class="stat-label">Notes</div>
      </div>
      <div class="stat">
        <div class="stat-value">{cats_with_notes}</div>
        <div class="stat-label">Categories</div>
      </div>
      <div class="stat">
        <div class="stat-value">{avg_rel:.1f}</div>
        <div class="stat-label">Avg Relevance</div>
      </div>
    </div>

    <!-- Search -->
    <div class="search-wrap">
      <i class="ph ph-magnifying-glass search-icon"></i>
      <input type="text" class="search-input" placeholder="Search notes..." id="searchInput">
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
      <p style="margin-top:6px">
        Built with <a href="https://github.com/dartaryan/tiktok-pipeline">TikTok Knowledge Pipeline</a>
      </p>
    </footer>
  </div>

  <script>
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
        c.style.display = catOk && searchOk ? '' : 'none';
        if (catOk && searchOk) vis++;
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

    function toggleCard(btn) {{
      const card = btn.closest('.card');
      const details = card.querySelector('.card-details');
      const open = details.style.display !== 'none';
      details.style.display = open ? 'none' : '';
      btn.classList.toggle('open', !open);
    }}
  </script>
</body>
</html>"""
