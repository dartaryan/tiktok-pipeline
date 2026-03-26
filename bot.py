"""Telegram bot for TikTok Knowledge Pipeline."""

import re
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

from src.config import validate_config, CATEGORIES, CATEGORY_EMOJIS
from src.downloader import download_audio, cleanup
from src.transcriber import transcribe
from src.processor import process_transcript
from src.formatter import to_markdown, generate_filepath
from src.storage import save_to_github, update_index

import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
# Optional: restrict to your user ID only
ALLOWED_USER_IDS = os.getenv("ALLOWED_USER_IDS", "")  # comma-separated, e.g. "123456,789012"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIKTOK_URL_PATTERN = re.compile(
    r'https?://(?:www\.|vm\.|vt\.)?tiktok\.com/\S+'
)


def is_allowed(user_id: int) -> bool:
    """Check if user is allowed to use the bot."""
    if not ALLOWED_USER_IDS:
        return True  # No restriction
    allowed = [int(uid.strip()) for uid in ALLOWED_USER_IDS.split(",") if uid.strip()]
    return user_id in allowed


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "🎬 TikTok Knowledge Pipeline\n\n"
        "שלח לי לינק של TikTok ואני אתמלל, אסווג ואשמור לך את זה ב-GitHub.\n\n"
        "Just forward or paste a TikTok link!"
    )


async def process_tiktok_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process a message containing a TikTok URL."""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    text = update.message.text or update.message.caption or ""
    urls = TIKTOK_URL_PATTERN.findall(text)

    if not urls:
        return  # Not a TikTok link, ignore silently

    for url in urls:
        status_msg = await update.message.reply_text(f"⏳ Processing...\n{url}")

        try:
            # Step 1: Download
            await status_msg.edit_text("📥 Downloading audio...")
            meta = download_audio(url)

            # Step 2: Transcribe
            await status_msg.edit_text("🎙️ Transcribing...")
            transcript = transcribe(meta.audio_path, language="en")

            # Step 3: Process with Claude
            await status_msg.edit_text("🧠 Analyzing with Claude...")
            note = process_transcript(
                transcript=transcript,
                source_url=url,
                creator=meta.creator,
                duration=meta.duration,
            )

            # Step 4: Format
            markdown = to_markdown(
                note=note,
                source_url=url,
                creator=meta.creator,
            )
            filepath = generate_filepath(note)

            # Step 5: Save to GitHub
            await status_msg.edit_text("📤 Saving to GitHub...")
            file_url = save_to_github(filepath, markdown, note.title_he)

            # Step 6: Update index
            try:
                update_index()
            except Exception:
                pass  # Non-critical

            # Step 7: Done!
            emoji = CATEGORY_EMOJIS.get(note.category, "📄")
            cat_he = CATEGORIES.get(note.category, {}).get("he", note.category)
            stars = "⭐" * note.relevance

            await status_msg.edit_text(
                f"✅ Done!\n\n"
                f"📌 {note.title_he}\n"
                f"{emoji} {cat_he}\n"
                f"{stars}\n\n"
                f"🔗 {file_url}"
            )

            # Cleanup
            cleanup(meta.video_id)

        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            await status_msg.edit_text(f"❌ Error:\n{str(e)[:200]}")


def main():
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    validate_config()

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        process_tiktok_link,
    ))

    logger.info("🤖 Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
