import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from deep_translator import GoogleTranslator

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    await update.message.reply_text(
        "🌍 Translation Bot Ready!\n\n"
        "Just send me text to translate to English.\n"
        "Or specify language: /tr <lang> <text>\n"
        "Example: /tr es Hello"
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle translation requests"""
    try:
        text = update.message.text
        
        if text.startswith('/tr'):
            parts = text.split(' ', 2)
            if len(parts) == 3:
                dest_lang = parts[1]
                text_to_translate = parts[2]
            else:
                await update.message.reply_text("⚠️ Format: /tr <lang> <text>")
                return
        else:
            dest_lang = 'en'
            text_to_translate = text
        
        translation = GoogleTranslator(
            source='auto',
            target=dest_lang
        ).translate(text_to_translate)
        
        await update.message.reply_text(
            f"🔤 Translation ({dest_lang.upper()}):\n{translation}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main() -> None:
    """Run the bot"""
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tr", translate_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    
    print("🟢 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
