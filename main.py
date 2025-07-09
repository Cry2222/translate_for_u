import os, logging
from flask import Flask, request
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext
from deep_translator import GoogleTranslator

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = set(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # e.g., "12345,67890"
DEFAULT_LANG = "my"  # Myanmar code

# Supported languages (code:name)
LANGUAGES = {
    "en": "English", "zh": "Chinese", "es": "Spanish",
    "fr": "French",  "de": "German",  "ja": "Japanese",
    # … add up to 20+ codes …
    "my": "Myanmar"
}

app = Flask(__name__)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, None, use_context=True)

# Helpers
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def make_lang_keyboard():
    keys = [
        InlineKeyboardButton(f"{code} – {name}", callback_data=f"SETLANG|{code}")
        for code, name in LANGUAGES.items()
    ]
    # two columns
    keyboard = [keys[i:i+2] for i in range(0, len(keys), 2)]
    return InlineKeyboardMarkup(keyboard)

# Command Handlers
def start(update: Update, context: CallbackContext):
    text = (
        "🤖🌍 Welcome to Translate For U!\n\n"
        "I'm your Myanmar translation assistant. Send any text—I auto-detect and translate it to Myanmar."
    )
    update.message.reply_text(text)

def help_cmd(update: Update, context: CallbackContext):
    help_text = (
        "/start - Welcome message\n"
        "/help - This help message\n"
        "/translate <text> - Translate specific text\n"
        "/languages - List supported languages\n"
        "/setlang <code> - Set preferred output language\n\n"
        "Or just send any text for instant translation!"
    )
    update.message.reply_text(help_text)

def languages(update: Update, context: CallbackContext):
    lines = [f"{code} — {name}" for code, name in LANGUAGES.items()]
    update.message.reply_text("Supported languages:\n" + "\n".join(lines))

def setlang(update: Update, context: CallbackContext):
    user = update.effective_user
    code = context.args[0].lower() if context.args else None
    if code in LANGUAGES:
        context.user_data["target_lang"] = code
        update.message.reply_text(f"✅ Output language set to {LANGUAGES[code]}")
    else:
        update.message.reply_text("❌ Invalid code. Use /languages to view codes.")

def translate(update: Update, context: CallbackContext):
    text = " ".join(context.args)
    if not text:
        return update.message.reply_text("Usage: /translate <text>")
    target = context.user_data.get("target_lang", DEFAULT_LANG)
    try:
        result = GoogleTranslator(source='auto', target=target).translate(text)
        update.message.reply_text(result)
    except Exception as e:
        logger.error(e)
        update.message.reply_text("⚠️ Translation failed. Try again.")

def broadcast(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    if not is_admin(uid):
        return update.message.reply_text("🚫 Unauthorized.")
    msg = " ".join(context.args)
    for user_id in context.bot_data.get("users", []):
        try:
            context.bot.send_message(user_id, f"📢 Broadcast:\n\n{msg}")
        except:
            pass
    update.message.reply_text("✅ Broadcast sent.")

def handle_text(update: Update, context: CallbackContext):
    uid = update.effective_user.id
    context.bot_data.setdefault("users", set()).add(uid)
    # Auto-translate incoming text
    text = update.message.text
    target = context.user_data.get("target_lang", DEFAULT_LANG)
    try:
        tr = GoogleTranslator(source='auto', target=target).translate(text)
        update.message.reply_text(tr)
    except:
        update.message.reply_text("⚠️ Could not translate.")

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data.split("|")
    if data[0] == "SETLANG" and data[1] in LANGUAGES:
        context.user_data["target_lang"] = data[1]
        query.answer(f"Language set to {LANGUAGES[data[1]]}")
        query.edit_message_text(f"✅ Preferred output: {LANGUAGES[data[1]]}")

# Register handlers
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("help", help_cmd))
dp.add_handler(CommandHandler("languages", languages))
dp.add_handler(CommandHandler("setlang", setlang))
dp.add_handler(CommandHandler("translate", translate))
dp.add_handler(CommandHandler("broadcast", broadcast))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
dp.add_handler(MessageHandler(Filters.callback_query, button_handler))

# Webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return "OK"

if __name__ == "__main__":
    # Set webhook once, then run Flask
    bot.set_webhook(f"https://<your-pyanywhere-username>.pythonanywhere.com/{TOKEN}")
    app.run(port=8443)

