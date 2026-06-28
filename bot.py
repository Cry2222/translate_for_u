import os
import logging
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from deep_translator import GoogleTranslator
from langdetect import detect, DetectorFactory

# Initialize deterministic language detection
DetectorFactory.seed = 0

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Supported languages with emoji flags
SUPPORTED_LANGUAGES = {
    '🇬🇧 English': 'en',
    '🇪🇸 Spanish': 'es',
    '🇫🇷 French': 'fr',
    '🇩🇪 German': 'de',
    '🇮🇹 Italian': 'it',
    '🇵🇹 Portuguese': 'pt',
    '🇷🇺 Russian': 'ru',
    '🇨🇳 Chinese': 'zh',
    '🇯🇵 Japanese': 'ja',
    '🇰🇷 Korean': 'ko',
    '🇲🇲 Myanmar': 'my',
    '🇸🇦 Arabic': 'ar',
    '🇮🇳 Hindi': 'hi',
    '🇻🇳 Vietnamese': 'vi',
    '🇹🇭 Thai': 'th',
    '🇮🇩 Indonesian': 'id',
}

DEFAULT_LANG = 'my'  # Default output language
TELEGRAM_MAX_MESSAGE_LENGTH = 4096

def get_language_keyboard():
    """Build responsive language selection keyboard, 2 columns for compactness"""
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    buttons = [lang_list[i:i + 2] for i in range(0, len(lang_list), 2)]
    buttons.append([KeyboardButton("↩️ Back")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)


def split_for_telegram(text: str, limit: int = TELEGRAM_MAX_MESSAGE_LENGTH):
    """Split a long string into Telegram-safe chunks, preferring paragraph/line/space breaks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        split_at = max(
            window.rfind('\n\n'),
            window.rfind('\n'),
            window.rfind('. '),
            window.rfind(' '),
        )
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with language keyboard"""
    await update.message.reply_text(
        "🌍 *Translate For U*\n\n"
        "Choose target language or send text to translate to Myanmar.\n"
        "Use /help for instructions.",
        reply_markup=get_language_keyboard(),
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help instructions"""
    await update.message.reply_text(
        "ℹ️ *How to Use*\n\n"
        "1. Tap a language to set target\n"
        "2. Send/forward text to translate\n"
        "3. Use `/tr es Hello` for quick translations\n"
        "4. Myanmar → English auto-detection\n\n"
        "Supported languages:\n" + 
        "\n".join(f"- {lang}" for lang in SUPPORTED_LANGUAGES),
        parse_mode='Markdown',
        reply_markup=get_language_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all incoming messages"""
    try:
        message = update.message
        if not message:
            return

        # Handle language selection
        if message.text in SUPPORTED_LANGUAGES:
            lang_code = SUPPORTED_LANGUAGES[message.text]
            context.user_data['target_lang'] = lang_code
            await message.reply_text(
                f"✅ Set to: {message.text}\nNow send text to translate.",
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("↩️ Back")]], resize_keyboard=True)
            )
            return

        # Handle back button
        if message.text == "↩️ Back":
            await start(update, context)
            return

        # Extract text from message or caption
        text = message.text or message.caption
        if not text:
            await message.reply_text("⚠️ Please send text or image with caption.")
            return

        # Handle /tr command
        if text.startswith('/tr'):
            parts = text.split(' ', 2)
            if len(parts) == 3:
                dest_lang = parts[1]
                text_to_translate = parts[2]
            else:
                await message.reply_text("⚠️ Format: `/tr es Hello`", parse_mode='Markdown')
                return
        else:
            dest_lang = context.user_data.get('target_lang', DEFAULT_LANG)
            text_to_translate = text

        # Auto-detect source (minimum 4 characters for reliable detection)
        detected = None
        if len(text_to_translate) >= 4:
            try:
                detected = detect(text_to_translate)
                if detected == 'my' and dest_lang == 'my':
                    dest_lang = 'en'
            except Exception as e:
                logger.warning(f"Detection failed: {e}")

        # Perform translation
        translated = GoogleTranslator(
            source='auto',
            target=dest_lang
        ).translate(text_to_translate)

        if not translated:
            await message.reply_text(
                "⚠️ Empty result. Try a different language or shorter text.",
                reply_markup=get_language_keyboard()
            )
            return

        direction = (
            f"{detected.upper()} → {dest_lang.upper()}"
            if detected else dest_lang.upper()
        )
        header = f"🔤 {direction}\n\n"
        chunks = split_for_telegram(header + translated)
        last_idx = len(chunks) - 1
        for i, chunk in enumerate(chunks):
            await message.reply_text(
                chunk,
                reply_markup=get_language_keyboard() if i == last_idx else None
            )

    except Exception as e:
        logger.error(f"Error: {e}")
        await message.reply_text(
            "❌ Translation failed. Try again or /help",
            reply_markup=get_language_keyboard()
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors and notify user"""
    logger.error(f"Error: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ Service temporary unavailable. Please try later.",
            reply_markup=get_language_keyboard()
        )

def main() -> None:
    """Start the bot"""
    app = Application.builder().token(TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("tr", handle_message))
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, handle_message))
    app.add_error_handler(error_handler)

    logger.info("🟢 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
