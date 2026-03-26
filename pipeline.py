#!/usr/bin/env python3
"""
TikTok Knowledge Extraction Pipeline — Phase 1 (Manual CLI)

Usage:
    python pipeline.py <tiktok_url>
    python pipeline.py <tiktok_url> --local    # Save locally instead of GitHub
    python pipeline.py --init                   # Set up GitHub repo structure
    python pipeline.py --batch urls.txt         # Process multiple URLs from file

Examples:
    python pipeline.py "https://www.tiktok.com/@user/video/123456"
    python pipeline.py "https://vm.tiktok.com/ABC123/"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

from src.config import validate_config, WORK_DIR
from src.downloader import download_audio, cleanup
from src.transcriber import transcribe
from src.processor import process_transcript
from src.formatter import to_markdown, generate_filepath
from src.storage import save_to_github, ensure_repo_structure, update_index


def process_url(url: str, save_local: bool = False) -> dict:
    """
    Process a single TikTok URL through the full pipeline.

    Returns a dict with the results for logging/reporting.
    """
    result = {
        "url": url,
        "status": "error",
        "title": None,
        "category": None,
        "relevance": None,
        "output_path": None,
        "error": None,
    }

    try:
        # Step 1: Download audio
        meta = download_audio(url)
        result["title"] = meta.title

        # Step 2: Transcribe
        transcript = transcribe(meta.audio_path, language="en")

        # Step 3: Process with Claude
        note = process_transcript(
            transcript=transcript,
            source_url=url,
            creator=meta.creator,
            duration=meta.duration,
        )
        result["category"] = note.category
        result["relevance"] = note.relevance
        result["title"] = note.title_he

        # Step 4: Format as markdown
        markdown = to_markdown(
            note=note,
            source_url=url,
            creator=meta.creator,
        )
        filepath = generate_filepath(note)

        # Step 5: Save
        if save_local:
            # Save to local file for testing
            local_dir = Path("output") / note.category
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / filepath.split("/")[-1]
            local_path.write_text(markdown, encoding="utf-8")
            result["output_path"] = str(local_path)
            print(f"\n📄 Saved locally: {local_path}")
        else:
            # Push to GitHub
            file_url = save_to_github(filepath, markdown, note.title_he)
            result["output_path"] = file_url
            # Update repo index
            try:
                update_index()
                print(f"📇 Index updated")
            except Exception as idx_err:
                print(f"⚠️ Index update failed: {idx_err}")
            print(f"\n🔗 GitHub: {file_url}")

        result["status"] = "success"

        # Cleanup temp files
        cleanup(meta.video_id)

    except Exception as e:
        result["error"] = str(e)
        print(f"\n❌ Error: {e}")

    return result


def process_batch(filepath: str, save_local: bool = False):
    """Process multiple URLs from a text file (one URL per line)."""
    urls_file = Path(filepath)
    if not urls_file.exists():
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    urls = [
        line.strip()
        for line in urls_file.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    print(f"\n📋 Processing {len(urls)} URLs...\n")
    results = []

    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"  [{i}/{len(urls)}] {url}")
        print(f"{'='*60}\n")
        result = process_url(url, save_local=save_local)
        results.append(result)

    # Print summary
    print(f"\n\n{'='*60}")
    print(f"  SUMMARY")
    print(f"{'='*60}")
    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "error")
    print(f"  ✅ Success: {success}")
    print(f"  ❌ Failed:  {failed}")

    for r in results:
        icon = "✅" if r["status"] == "success" else "❌"
        title = r["title"] or r["url"][:50]
        cat = r["category"] or "—"
        rel = r["relevance"] or "—"
        print(f"  {icon} [{cat}] (rel:{rel}) {title}")
        if r["error"]:
            print(f"     Error: {r['error']}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="TikTok Knowledge Extraction Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py "https://www.tiktok.com/@user/video/123"
  python pipeline.py "https://vm.tiktok.com/ABC/" --local
  python pipeline.py --batch urls.txt
  python pipeline.py --init
        """,
    )

    parser.add_argument(
        "url",
        nargs="?",
        help="TikTok video URL to process",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Save output locally instead of pushing to GitHub",
    )
    parser.add_argument(
        "--batch",
        metavar="FILE",
        help="Process multiple URLs from a text file (one per line)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize GitHub repo folder structure",
    )

    args = parser.parse_args()

    # Validate environment
    if not args.local:
        validate_config()
    else:
        # For local mode, only need Groq + Anthropic keys
        from src.config import GROQ_API_KEY, ANTHROPIC_API_KEY
        if not GROQ_API_KEY or not ANTHROPIC_API_KEY:
            print("❌ Missing GROQ_API_KEY or ANTHROPIC_API_KEY in .env")
            sys.exit(1)

    if args.init:
        print("🔧 Initializing GitHub repo structure...")
        ensure_repo_structure()
        print("✅ Done!")
        return

    if args.batch:
        process_batch(args.batch, save_local=args.local)
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    # Single URL processing
    print(f"\n🚀 TikTok Knowledge Pipeline")
    print(f"   URL: {args.url}")
    print(f"   Mode: {'Local' if args.local else 'GitHub'}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    result = process_url(args.url, save_local=args.local)

    if result["status"] == "success":
        print(f"\n🎉 Done! Category: {result['category']}, Relevance: {result['relevance']}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
