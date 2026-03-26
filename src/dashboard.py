"""Generate a TikTok-branded HTML dashboard for the knowledge base."""

from datetime import datetime
from .config import CATEGORIES

# TikTok brand colors
COLORS = {
    "bg": "#000000",
    "surface": "#161823",
    "surface2": "#1e2030",
    "pink": "#FE2C55",
    "cyan": "#25F4EE",
    "white": "#FFFFFF",
    "gray": "#8A8B91",
    "gray_dark": "#2C2D35",
    "border": "rgba(255,255,255,0.08)",
}

# Phosphor icon mapping per category (replacing emojis)
CATEGORY_ICONS = {
    "elon-katzef": "ph-brain",
    "shalhevet": "ph-flame",
    "taylor-played": "ph-game-controller",
    "optiplan": "ph-buildings",
    "other": "ph-package",
}

# Phosphor icon for relevance stars
STAR_ICON = "ph-star-fill"


def _build_note_card(note: dict) -> str:
    """Build HTML for a single note card."""
    cat_key = note.get("_category", "other")
    cat_info = CATEGORIES.get(cat_key, {})
    cat_he = cat_info.get("he", cat_key)
    cat_en = cat_info.get("en", cat_key)
    icon_class = CATEGORY_ICONS.get(cat_key, "ph-file-text")

    title_he = note.get("title_he", "---")
    title_en = note.get("title_en", "---")
    date = note.get("date_processed", "---")
    source = note.get("source", "#")
    relevance = note.get("relevance", 3)
    rel = int(relevance) if isinstance(relevance, (int, float)) else 3

    stars_html = f'<i class="{STAR_ICON}"></i> ' * rel
    tags = note.get("tags", "")

    # Parse tags from frontmatter string format
    tags_html = ""
    if tags and isinstance(tags, str):
        tag_list = [t.strip().strip('"').strip("'") for t in tags.strip("[]").split(",") if t.strip()]
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in tag_list[:4])

    return f"""
    <article class="card" data-category="{cat_key}" data-relevance="{rel}">
      <div class="card-header">
        <div class="card-icon"><i class="{icon_class}"></i></div>
        <div class="card-meta">
          <span class="card-category">{cat_he} / {cat_en}</span>
          <span class="card-date"><i class="ph-calendar-blank"></i> {date}</span>
        </div>
      </div>
      <h3 class="card-title-he">{title_he}</h3>
      <p class="card-title-en">{title_en}</p>
      <div class="card-footer">
        <div class="card-relevance">{stars_html}</div>
        <div class="card-tags">{tags_html}</div>
        <a href="{source}" target="_blank" rel="noopener" class="card-source">
          <i class="ph-arrow-square-out"></i> Source
        </a>
      </div>
    </article>"""


def _build_category_filter(notes: list) -> str:
    """Build the category filter bar."""
    buttons = ['<button class="filter-btn active" data-filter="all"><i class="ph-squares-four"></i> All</button>']
    for cat_key, cat_info in CATEGORIES.items():
        count = sum(1 for n in notes if n.get("_category") == cat_key)
        if count == 0:
            continue
        icon = CATEGORY_ICONS.get(cat_key, "ph-file-text")
        buttons.append(
            f'<button class="filter-btn" data-filter="{cat_key}">'
            f'<i class="{icon}"></i> {cat_info["en"]} <span class="count">{count}</span>'
            f'</button>'
        )
    return "\n".join(buttons)


def generate_dashboard_html(notes: list) -> str:
    """Generate the full HTML dashboard page."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(notes)
    cats_with_notes = len(set(n.get("_category") for n in notes))

    # Sort by date newest first
    notes_sorted = sorted(notes, key=lambda n: n.get("date_processed", ""), reverse=True)

    cards_html = "\n".join(_build_note_card(n) for n in notes_sorted)
    filters_html = _build_category_filter(notes_sorted)

    # Stats
    avg_relevance = sum(
        int(n.get("relevance", 3)) if isinstance(n.get("relevance", 3), (int, float)) else 3
        for n in notes
    ) / max(total, 1)

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TikTok Knowledge Base</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/@phosphor-icons/web"></script>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: {COLORS["bg"]};
      --surface: {COLORS["surface"]};
      --surface2: {COLORS["surface2"]};
      --pink: {COLORS["pink"]};
      --cyan: {COLORS["cyan"]};
      --white: {COLORS["white"]};
      --gray: {COLORS["gray"]};
      --gray-dark: {COLORS["gray_dark"]};
      --border: {COLORS["border"]};
      --radius: 12px;
    }}

    body {{
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--white);
      min-height: 100vh;
      direction: rtl;
    }}

    /* --- Hero --- */
    .hero {{
      position: relative;
      padding: 60px 24px 40px;
      text-align: center;
      overflow: hidden;
    }}

    .hero::before {{
      content: '';
      position: absolute;
      top: -50%;
      left: -20%;
      width: 60%;
      height: 200%;
      background: radial-gradient(ellipse, rgba(254,44,85,0.15) 0%, transparent 60%);
      pointer-events: none;
    }}

    .hero::after {{
      content: '';
      position: absolute;
      top: -50%;
      right: -20%;
      width: 60%;
      height: 200%;
      background: radial-gradient(ellipse, rgba(37,244,238,0.1) 0%, transparent 60%);
      pointer-events: none;
    }}

    .hero-logo {{
      display: inline-flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      position: relative;
    }}

    .hero-logo .logo-icon {{
      font-size: 40px;
      color: var(--white);
      position: relative;
    }}

    .hero-logo .logo-icon::before {{
      content: '';
      position: absolute;
      inset: -4px;
      background: linear-gradient(135deg, var(--cyan), var(--pink));
      border-radius: 10px;
      z-index: -1;
      opacity: 0.3;
      filter: blur(8px);
    }}

    .hero h1 {{
      font-size: clamp(28px, 5vw, 42px);
      font-weight: 700;
      letter-spacing: -0.5px;
      position: relative;
    }}

    .hero h1 .accent-pink {{ color: var(--pink); }}
    .hero h1 .accent-cyan {{ color: var(--cyan); }}

    .hero-subtitle {{
      color: var(--gray);
      font-size: 16px;
      margin-top: 8px;
      position: relative;
    }}

    /* --- Stats --- */
    .stats {{
      display: flex;
      justify-content: center;
      gap: 32px;
      padding: 24px;
      position: relative;
    }}

    .stat {{
      text-align: center;
    }}

    .stat-value {{
      font-size: 28px;
      font-weight: 700;
      color: var(--white);
    }}

    .stat-value.pink {{ color: var(--pink); }}
    .stat-value.cyan {{ color: var(--cyan); }}

    .stat-label {{
      font-size: 12px;
      color: var(--gray);
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-top: 4px;
    }}

    /* --- Filters --- */
    .filters {{
      display: flex;
      gap: 8px;
      padding: 16px 24px;
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
      padding: 8px 16px;
      border: 1px solid var(--border);
      border-radius: 100px;
      background: transparent;
      color: var(--gray);
      font-family: inherit;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s ease;
      white-space: nowrap;
    }}

    .filter-btn:hover {{
      border-color: var(--gray-dark);
      color: var(--white);
    }}

    .filter-btn.active {{
      background: var(--white);
      color: var(--bg);
      border-color: var(--white);
    }}

    .filter-btn .count {{
      background: var(--gray-dark);
      padding: 1px 7px;
      border-radius: 100px;
      font-size: 11px;
    }}

    .filter-btn.active .count {{
      background: rgba(0,0,0,0.15);
    }}

    /* --- Divider --- */
    .divider {{
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--gray-dark), transparent);
      margin: 0 24px;
    }}

    /* --- Cards Grid --- */
    .cards-container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }}

    .cards-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
      gap: 16px;
    }}

    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 20px;
      transition: all 0.25s ease;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }}

    .card:hover {{
      border-color: var(--gray-dark);
      transform: translateY(-2px);
      box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }}

    .card-header {{
      display: flex;
      align-items: center;
      gap: 12px;
    }}

    .card-icon {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      background: var(--surface2);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: var(--cyan);
      flex-shrink: 0;
    }}

    .card[data-category="elon-katzef"] .card-icon {{ color: var(--cyan); }}
    .card[data-category="shalhevet"] .card-icon {{ color: #FF6B35; }}
    .card[data-category="taylor-played"] .card-icon {{ color: #A855F7; }}
    .card[data-category="optiplan"] .card-icon {{ color: var(--pink); }}
    .card[data-category="other"] .card-icon {{ color: var(--gray); }}

    .card-meta {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      min-width: 0;
    }}

    .card-category {{
      font-size: 12px;
      font-weight: 600;
      color: var(--gray);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}

    .card-date {{
      font-size: 11px;
      color: var(--gray-dark);
      display: flex;
      align-items: center;
      gap: 4px;
    }}

    .card-title-he {{
      font-size: 17px;
      font-weight: 600;
      line-height: 1.5;
      color: var(--white);
    }}

    .card-title-en {{
      font-size: 13px;
      color: var(--gray);
      line-height: 1.4;
    }}

    .card-footer {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: auto;
      padding-top: 12px;
      border-top: 1px solid var(--border);
      flex-wrap: wrap;
    }}

    .card-relevance {{
      color: #FBBF24;
      font-size: 12px;
      display: flex;
      gap: 1px;
    }}

    .card-tags {{
      display: flex;
      gap: 4px;
      flex-wrap: wrap;
      flex: 1;
    }}

    .tag {{
      padding: 2px 8px;
      border-radius: 100px;
      font-size: 11px;
      background: var(--surface2);
      color: var(--gray);
      border: 1px solid var(--border);
    }}

    .card-source {{
      color: var(--cyan);
      font-size: 12px;
      font-weight: 500;
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: opacity 0.2s;
      margin-inline-start: auto;
    }}

    .card-source:hover {{ opacity: 0.7; }}

    /* --- Empty state --- */
    .empty {{
      text-align: center;
      padding: 60px 24px;
      color: var(--gray);
    }}

    .empty i {{ font-size: 48px; margin-bottom: 16px; display: block; }}

    /* --- Footer --- */
    footer {{
      text-align: center;
      padding: 40px 24px;
      color: var(--gray-dark);
      font-size: 12px;
    }}

    footer a {{ color: var(--gray); text-decoration: none; }}
    footer a:hover {{ color: var(--white); }}

    /* --- Search --- */
    .search-container {{
      max-width: 480px;
      margin: 0 auto;
      padding: 0 24px 8px;
      position: relative;
    }}

    .search-input {{
      width: 100%;
      padding: 12px 16px 12px 44px;
      border-radius: 100px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--white);
      font-family: inherit;
      font-size: 14px;
      outline: none;
      transition: border-color 0.2s;
    }}

    .search-input::placeholder {{ color: var(--gray-dark); }}
    .search-input:focus {{ border-color: var(--gray-dark); }}

    .search-icon {{
      position: absolute;
      left: auto;
      right: 40px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--gray);
      font-size: 18px;
      pointer-events: none;
    }}

    /* --- Responsive --- */
    @media (max-width: 640px) {{
      .cards-grid {{ grid-template-columns: 1fr; }}
      .stats {{ gap: 20px; }}
      .hero {{ padding: 40px 16px 24px; }}
    }}

    /* --- Animations --- */
    @keyframes fadeUp {{
      from {{ opacity: 0; transform: translateY(16px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}

    .card {{
      animation: fadeUp 0.4s ease backwards;
    }}

    .card:nth-child(1) {{ animation-delay: 0.03s; }}
    .card:nth-child(2) {{ animation-delay: 0.06s; }}
    .card:nth-child(3) {{ animation-delay: 0.09s; }}
    .card:nth-child(4) {{ animation-delay: 0.12s; }}
    .card:nth-child(5) {{ animation-delay: 0.15s; }}
    .card:nth-child(6) {{ animation-delay: 0.18s; }}
    .card:nth-child(7) {{ animation-delay: 0.21s; }}
    .card:nth-child(8) {{ animation-delay: 0.24s; }}
    .card:nth-child(9) {{ animation-delay: 0.27s; }}
  </style>
</head>
<body>

  <!-- Hero -->
  <section class="hero">
    <div class="hero-logo">
      <span class="logo-icon"><i class="ph-fill ph-video"></i></span>
    </div>
    <h1><span class="accent-pink">TikTok</span> <span class="accent-cyan">Knowledge</span> Base</h1>
    <p class="hero-subtitle">Extracted insights from tech TikTok, powered by AI</p>
  </section>

  <!-- Stats -->
  <div class="stats">
    <div class="stat">
      <div class="stat-value pink">{total}</div>
      <div class="stat-label">Notes</div>
    </div>
    <div class="stat">
      <div class="stat-value cyan">{cats_with_notes}</div>
      <div class="stat-label">Categories</div>
    </div>
    <div class="stat">
      <div class="stat-value">{avg_relevance:.1f}</div>
      <div class="stat-label">Avg Relevance</div>
    </div>
  </div>

  <!-- Search -->
  <div class="search-container">
    <i class="ph-magnifying-glass search-icon"></i>
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
    <div class="empty" id="emptyState" style="display:none;">
      <i class="ph-magnifying-glass"></i>
      <p>No notes found</p>
    </div>
  </div>

  <!-- Footer -->
  <footer>
    <p>Last updated: {now}</p>
    <p style="margin-top:4px;">
      Built with <a href="https://github.com/dartaryan/tiktok-pipeline">TikTok Knowledge Pipeline</a>
    </p>
  </footer>

  <script>
    // --- Filter ---
    const filterBtns = document.querySelectorAll('.filter-btn');
    const cards = document.querySelectorAll('.card');
    const emptyState = document.getElementById('emptyState');
    const searchInput = document.getElementById('searchInput');

    let activeFilter = 'all';

    function applyFilters() {{
      const query = searchInput.value.toLowerCase().trim();
      let visible = 0;

      cards.forEach(card => {{
        const matchCategory = activeFilter === 'all' || card.dataset.category === activeFilter;
        const text = card.textContent.toLowerCase();
        const matchSearch = !query || text.includes(query);
        const show = matchCategory && matchSearch;
        card.style.display = show ? '' : 'none';
        if (show) visible++;
      }});

      emptyState.style.display = visible === 0 ? '' : 'none';
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
  </script>
</body>
</html>"""
