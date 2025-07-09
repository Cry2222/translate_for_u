import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from pygoogletrans import Translator

# Initialize translator
translator = Translator()

# Get token from environment variable
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message"""
    await update.message.reply_text(
        "Hi! I'm a translation bot. Send me text and I'll translate it to English.\n"
        "You can specify language like: /tr es Hello"
    )

async def translate_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle translation"""
    try:
        text = update.message.text
        
        if text.startswith('/tr'):
            parts = text.split(' ', 2)
            if len(parts) == 3:
                dest_lang = parts[1]
                text_to_translate = parts[2]
            else:
                await update.message.reply_text("Format: /tr <lang_code> <text>")
                return
        else:
            dest_lang = 'en'
            text_to_translate = text
        
        translation = translator.translate(text_to_translate, dest=dest_lang)
        await update.message.reply_text(
            f"Translation ({translation.src} → {dest_lang}):\n{translation.text}"
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main() -> None:
    """Run bot"""
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tr", translate_text))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, translate_text))
    
    print("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
