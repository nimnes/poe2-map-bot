from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from poe2_map_bot.bosses import BossBook, format_boss_guide, format_boss_list
from poe2_map_bot.maps import MapBook, escape_md, format_profile


LOGGER = logging.getLogger(__name__)


class BotState:
    def __init__(self, map_data_path: Path, boss_data_path: Path):
        self.map_data_path = map_data_path
        self.boss_data_path = boss_data_path
        self.map_book = MapBook.load(map_data_path)
        self.boss_book = BossBook.load(boss_data_path)

    def reload(self) -> None:
        self.map_book = MapBook.load(self.map_data_path)
        self.boss_book = BossBook.load(self.boss_data_path)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    await update.effective_message.reply_text(
        "Send a PoE 2 map name, or use /map <name>.\n"
        "Use /boss <name> for boss guides.\n"
        f"I currently know {len(state.map_book.profiles)} maps and {len(state.boss_book.guides)} bosses."
    )


async def maps_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    names = ", ".join(profile.name for profile in state.map_book.profiles)
    await update.effective_message.reply_text(f"Known maps:\n{names}")


async def bosses_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    await update.effective_message.reply_text(
        format_boss_list(state.boss_book.guides),
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def reload_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = get_state(context)
    state.reload()
    await update.effective_message.reply_text(
        f"Reloaded {len(state.map_book.profiles)} map profiles and {len(state.boss_book.guides)} boss guides."
    )


async def map_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text("Use /map <map name>, for example /map Augury")
        return
    await answer_query(update, context, query)


async def boss_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = " ".join(context.args).strip()
    if not query:
        await update.effective_message.reply_text("Use /boss <boss name>, for example /boss Arbiter")
        return
    await answer_boss_query(update, context, query)


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = (update.effective_message.text or "").strip()
    await answer_query(update, context, query)


async def answer_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> None:
    state = get_state(context)
    profile, suggestions = state.map_book.find(query)
    if profile:
        await update.effective_message.reply_text(
            format_profile(profile),
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        return

    suffix = ""
    if suggestions:
        suffix = "\n\nClosest matches:\n" + "\n".join(f"\\- {escape_md(item)}" for item in suggestions)
    await update.effective_message.reply_text(
        f"I do not know that map yet\\.{suffix}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


async def answer_boss_query(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str) -> None:
    state = get_state(context)
    guide, suggestions = state.boss_book.find(query)
    if guide:
        await update.effective_message.reply_text(
            format_boss_guide(guide),
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
        )
        return

    suffix = ""
    if suggestions:
        suffix = "\n\nClosest matches:\n" + "\n".join(f"\\- {escape_md(item)}" for item in suggestions)
    await update.effective_message.reply_text(
        f"I do not know that boss yet\\.{suffix}",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


def get_state(context: ContextTypes.DEFAULT_TYPE) -> BotState:
    return context.application.bot_data["state"]


def build_application() -> Application:
    load_dotenv()
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is required. Add it to .env or your shell environment.")

    map_data_path = Path(os.getenv("MAP_DATA_PATH", "data/maps.json")).resolve()
    boss_data_path = Path(os.getenv("BOSS_DATA_PATH", "data/bosses.json")).resolve()
    state = BotState(map_data_path, boss_data_path)

    application = Application.builder().token(token).build()
    application.bot_data["state"] = state
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("maps", maps_command))
    application.add_handler(CommandHandler("bosses", bosses_command))
    application.add_handler(CommandHandler("reload", reload_command))
    application.add_handler(CommandHandler("map", map_command))
    application.add_handler(CommandHandler("boss", boss_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))
    return application


def main() -> None:
    app = build_application()
    webhook_url = os.getenv("TELEGRAM_WEBHOOK_URL")
    if webhook_url:
        port = int(os.getenv("PORT", "8080"))
        webhook_path = os.getenv("TELEGRAM_WEBHOOK_PATH", "telegram")
        LOGGER.info("Starting PoE 2 map bot with webhook on port %s", port)
        app.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=webhook_path,
            webhook_url=f"{webhook_url.rstrip('/')}/{webhook_path}",
            allowed_updates=Update.ALL_TYPES,
        )
        return

    LOGGER.info("Starting PoE 2 map bot with polling")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
