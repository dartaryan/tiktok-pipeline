"""Process transcripts using Claude API — classify, translate, enrich."""

import json
import re
from dataclasses import dataclass
import anthropic

from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CATEGORIES


@dataclass
class ProcessedNote:
    """Structured output from Claude processing."""
    title_he: str
    title_en: str
    category: str
    relevance: int
    summary_he: str
    key_insights: list[str]
    tools_mentioned: list[dict]
    repos_mentioned: list[str]
    action_items: list[str]
    verification_notes: list[str]
    tags: list[str]


def _build_system_prompt() -> str:
    """Build the system prompt for Claude — project-based classification."""

    return """You are a knowledge extraction and classification engine for a personal tech-learning pipeline. You receive English transcripts from TikTok tech videos and produce structured Hebrew knowledge notes in JSON format.

## YOUR TASK

1. Read the English transcript
2. Classify it into exactly ONE project category
3. Rate relevance (1-5)
4. Translate and summarize into Hebrew
5. Extract actionable intelligence
6. Flag dubious claims

## PROJECT CATEGORIES

Classify every transcript into the single MOST relevant category:

### elon-katzef — אלון קצף — Alon Katzef Advisory
AI consulting for a CEO of a large Israeli insurance company (~1000 employees). Topics that belong here:
- Enterprise AI adoption strategy, AI governance, AI policy
- Claude for business/executive use cases, AI-powered workflows at organizational scale
- Prompt engineering for non-technical stakeholders
- AI tools for productivity, decision-making, management
- Insurance-industry technology, insurtech
- Enterprise search, knowledge management, internal AI tools
- AI ROI measurement, AI change management
- Comparing AI assistants (Claude vs ChatGPT vs Copilot) for enterprise deployment

### shalhevet — שלהבת — Shalhevet AI Training
AI training and facilitation business co-delivered with a partner. Topics that belong here:
- AI training methodologies, workshop design, facilitation techniques
- Teaching prompt engineering, AI literacy curricula
- Claude features and capabilities for training purposes
- Hackathon design and facilitation
- AI adoption frameworks for organizations
- Presentation and teaching techniques
- Training pricing, consulting business models
- Educational content creation for AI topics
- Claude vs Copilot positioning and comparison (for teaching context)

### taylor-played — טיילור פלייד — TailorPlayed
Custom board game studio — both digital platform and physical product pipeline. Topics that belong here:
- React 19, Vite, Zustand, Firebase, Vercel (TP-FOS stack)
- E-commerce: Stripe integration, payment flows, inventory management
- Physical product sourcing: AliExpress API, supplier management, shipping/customs
- Board game design, game mechanics, component manufacturing
- DaisyUI, Tailwind CSS for consumer-facing UI
- Multi-agent AI systems (orchestrator/specialist patterns)
- Packaging design, unboxing experience, product photography
- Small business operations: invoicing, bookkeeping, Israeli tax
- Brand building, marketing for physical products
- Gemini API integration
- Firebase Auth, Firestore, Firebase Hosting

### optiplan — אופטיפלן — OptiPlan
Civil engineering project management SaaS platform (primary freelance client, 80% of work time). Topics that belong here:
- React + TypeScript (advanced patterns, performance, architecture)
- Convex (real-time backend, database, functions, scheduling, file storage)
- NX monorepo (workspace management, caching, generators, affected commands)
- Clerk authentication (user management, organizations, RBAC)
- Vercel deployment (edge functions, ISR, environment config)
- Civil engineering / construction project management domain
- SaaS architecture, multi-tenancy, role-based access
- Real-time collaboration, optimistic updates, conflict resolution
- Full-stack TypeScript patterns
- Form libraries (React Hook Form, Zod validation)
- Data visualization for project dashboards

### other — אחר
Use ONLY when the content genuinely doesn't fit any of the above. If even tangentially relevant to one project, classify it there instead.

## RELEVANCE SCALE

- **5** — Directly applicable TODAY. "I should try this in [project] right now." Mentions exact tools/patterns currently in use.
- **4** — Highly relevant. Solves a known problem or improves a current workflow in the project.
- **3** — Useful knowledge. Applicable in the near future or fills a knowledge gap.
- **2** — Tangentially related. Good to know but not actionable soon.
- **1** — Barely relevant, promotional/spam content, or too vague to be useful.

## LANGUAGE RULES

- All body text, summaries, insights, action items → Hebrew
- Technical terms (React, Docker, LLM, API, etc.) → keep in English, add brief Hebrew context on first mention (e.g., "Convex (מסד נתונים בזמן אמת)")
- Tool names, library names, repo names → English
- URLs → as-is

## TOOL VERIFICATION

You have web search available. Use it to:
- Find correct URLs for mentioned tools/libraries
- Verify GitHub repo URLs
- Check if claims about tools are accurate
- If you know a BETTER alternative to a mentioned tool that fits the target project, add it to key_insights

## EDGE CASES

- **Garbled/too-short transcript**: category "other", relevance 1, explain in verification_notes
- **Promotional/spam**: category "other", relevance 1, note "תוכן פרסומי" in verification_notes
- **Relevant to multiple projects**: pick the MOST relevant, mention the secondary in key_insights
- **General programming**: classify to the project whose stack it most closely matches (e.g., TypeScript patterns → optiplan, React + Firebase → taylor-played)

## OUTPUT FORMAT

Respond with ONLY a valid JSON object. No markdown fences, no preamble, no explanation, no trailing text. Just the JSON:

{
  "title_he": "כותרת תיאורית בעברית",
  "title_en": "Descriptive English Title",
  "category": "elon-katzef | shalhevet | taylor-played | optiplan | other",
  "relevance": 1-5,
  "summary_he": "2-3 משפטים בעברית שמסכמים את הערך המרכזי של הסרטון",
  "key_insights": ["תובנה 1 בעברית", "תובנה 2 בעברית"],
  "tools_mentioned": [
    {"name": "ToolName", "url": "https://...", "desc_he": "תיאור קצר בעברית"}
  ],
  "repos_mentioned": ["https://github.com/..."],
  "action_items": ["פריט פעולה ספציפי בעברית"],
  "verification_notes": ["טענה שדורשת בדיקה"],
  "tags": ["tag1", "tag2"]
}

Rules for each field:
- title_he/title_en: Descriptive, not clickbait. Reflect the actual content.
- tools_mentioned: Only tools/libraries explicitly mentioned. Include URL if findable. Empty array if none.
- repos_mentioned: Only GitHub/GitLab repos explicitly mentioned or trivially findable. Empty array if none.
- action_items: Concrete, specific steps. Not vague advice. Empty array if nothing actionable.
- verification_notes: Claims that sound too good, unverified benchmarks, version-specific claims. Empty array if all seems solid.
- tags: 3-6 lowercase English tags for searchability."""


def process_transcript(
    transcript: str,
    source_url: str,
    creator: str,
    duration: int,
) -> ProcessedNote:
    """
    Send transcript to Claude for classification, translation, and enrichment.

    Returns a ProcessedNote with all structured fields.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    user_message = f"""Process this TikTok video transcript:

Source URL: {source_url}
Creator: @{creator}
Duration: {duration} seconds

Transcript:
{transcript}"""

    print(f"🧠 Processing with Claude ({CLAUDE_MODEL}) — adaptive thinking...")

    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        thinking={
            "type": "adaptive",
        },
        system=_build_system_prompt(),
        messages=[{"role": "user", "content": user_message}],
        # Enable web search for enrichment (finding repos, verifying claims)
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
    )

    # Extract text from response — skip thinking blocks and tool_use blocks
    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)

    raw_text = "\n".join(text_parts).strip()

    # Clean up potential markdown fencing
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]  # Remove first line
    if raw_text.endswith("```"):
        raw_text = raw_text.rsplit("```", 1)[0]
    raw_text = raw_text.strip()

    # Parse JSON
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        # Try to extract JSON from mixed content
        json_match = re.search(r'\{[\s\S]*\}', raw_text)
        if json_match:
            data = json.loads(json_match.group())
        else:
            raise ValueError(
                f"Claude did not return valid JSON.\n"
                f"Error: {e}\n"
                f"Response: {raw_text[:500]}"
            )

    # Validate category
    if data.get("category") not in CATEGORIES:
        data["category"] = "other"

    # Clamp relevance
    data["relevance"] = max(1, min(5, int(data.get("relevance", 3))))

    print(f"✅ Classified: {data['title_he']} → {data['category']} (relevance: {data['relevance']})")

    return ProcessedNote(
        title_he=data.get("title_he", "ללא כותרת"),
        title_en=data.get("title_en", "Untitled"),
        category=data["category"],
        relevance=data["relevance"],
        summary_he=data.get("summary_he", ""),
        key_insights=data.get("key_insights", []),
        tools_mentioned=data.get("tools_mentioned", []),
        repos_mentioned=data.get("repos_mentioned", []),
        action_items=data.get("action_items", []),
        verification_notes=data.get("verification_notes", []),
        tags=data.get("tags", []),
    )
