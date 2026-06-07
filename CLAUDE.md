# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`translate_for_u` is a Telegram bot that provides real-time translation into 9 languages via an interactive keyboard UI. The entire bot logic lives in a single file: `bot.py`.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file (not committed) with:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

## Running the Bot

```bash
python bot.py
```

There is no build step, no test suite, and no linting configuration.

## Architecture

`bot.py` is the sole application file (~170 lines). It uses `python-telegram-bot==20.6` with its async `Application` builder pattern.

**Message flow:**
1. `/start` and `/help` commands present a language selection keyboard.
2. User taps a language button → `context.user_data['target_lang']` is updated (default: `my` for Myanmar).
3. Any subsequent text or image caption is passed to `deep_translator.GoogleTranslator` using the stored target language.
4. `/tr <lang_code> <text>` is a one-shot inline translation that bypasses the stored preference.

**Myanmar auto-switch:** When the detected source language is Myanmar (`my`) and the target is also Myanmar, the bot automatically switches the target to English (`en`) to avoid a no-op translation. `langdetect.DetectorFactory.seed = 0` is set for deterministic detection.

**Supported languages:** `en`, `es`, `fr`, `de`, `ru`, `zh`, `ja`, `ko`, `my`

**Key dependencies:**
- `python-telegram-bot==20.6` — async Telegram API wrapper
- `deep-translator==1.11.4` — Google Translate backend
- `langdetect==1.0.9` — source language detection
- `python-dotenv==1.0.0` — loads `TELEGRAM_BOT_TOKEN` from `.env`

## Key Conventions

- All handler functions are `async def` and follow the `(update, context)` signature required by `python-telegram-bot`.
- Per-user state is stored exclusively in `context.user_data` (no external database or cache).
- Translation errors are caught and surfaced to the user as a Telegram message; they do not crash the bot.
- The global error handler (`error_handler`) logs exceptions and notifies the user when possible.
- Keyboards use `resize_keyboard=True` for mobile-friendly rendering.
