"""
ikembubot - deletes messages containing links unless:
  - the sender is a group admin, OR
  - the link's domain is on that group's whitelist, OR
  - the group has turned the bot off with /toggle
"""

import logging
import os
import re
from urllib.parse import urlparse

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import Application, ContextTypes, MessageHandler, CommandHandler, filters

import storage

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

URL_REGEX = re.compile(
    r"(https?://\S+)|(www\.\S+)|(\bt\.me/\S+)|(\b[a-zA-Z0-9-]+\.(com|net|org|io|xyz|me|gg|co|ru|info)\b\S*)",
    re.IGNORECASE,
)


def find_links(update: Update) -> list[str]:
    msg = update.effective_message
    text = msg.text or msg.caption or ""
    links = [m.group(0) for m in URL_REGEX.finditer(text)]
    entities = list(msg.entities or []) + list(msg.caption_entities or [])
    for entity in entities:
        if entity.type == "text_link" and entity.url:
            links.append(entity.url)
    return links


def get_domain(link: str) -> str:
    if "//" not in link:
        link = "//" + link
    host = urlparse(link).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return False
    member = await context.bot.get_chat_member(chat.id, user.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def moderate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat is None or chat.type not in ("group", "supergroup"):
        return
    settings = storage.get_settings(chat.id)
    if not settings["enabled"]:
        return
    links = find_links(update)
    if not links:
        return
    whitelist_domains = settings["whitelist"]
    if all(get_domain(link) in whitelist_domains for link in links):
        return
    try:
        if await is_admin(update, context):
            return
    except Exception as e:
        logger.warning("Could not check admin status: %s", e)
        return
    try:
        await update.effective_message.delete()
        logger.info("Deleted link message from user %s in chat %s", update.effective_user.id, chat.id)
    except Exception as e:
        logger.warning("Could not delete message: %s", e)


async def require_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("This command only works inside a group.")
        return False
    if not await is_admin(update, context):
        await update.effective_message.reply_text("Only group admins can use this command.")
        return False
    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "Hi! I'm ikembubot.\n\n"
        "Add me to your group and make me an admin with 'Delete messages' "
        "permission. I'll automatically remove any message containing a "
        "link unless it's posted by a group admin.\n\n"
        "Group admins can use:\n"
        "/toggle - turn link-deleting on or off for this group\n"
        "/status - check current settings\n"
        "/history - see who toggled the bot recently\n"
        "/whitelist add example.com - allow links from a domain\n"
        "/whitelist remove example.com - remove a domain\n"
        "/whitelist list - show allowed domains"
    )


async def toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update, context):
        return
    chat_id = update.effective_chat.id
    currently_enabled = storage.get_settings(chat_id)["enabled"]
    new_value = not currently_enabled
    storage.set_enabled(chat_id, new_value)
    actor = update.effective_user.full_name or update.effective_user.username or "Unknown admin"
    storage.log_toggle_action(chat_id, actor, new_value)
    await update.effective_message.reply_text(
        f"Link-deleting is now {'ON' if new_value else 'OFF'} for this group."
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type not in ("group", "supergroup"):
        await update.effective_message.reply_text("This command only works inside a group.")
        return
    settings = storage.get_settings(update.effective_chat.id)
    state = "ON" if settings["enabled"] else "OFF"
    domains = ", ".join(settings["whitelist"]) if settings["whitelist"] else "none"
    await update.effective_message.reply_text(f"Link-deleting: {state}\nWhitelisted domains: {domains}")


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update, context):
        return
    log = storage.get_toggle_log(update.effective_chat.id)
    if not log:
        await update.effective_message.reply_text("No toggle history yet for this group.")
        return
    lines = []
    for entry in reversed(log):
        state = "ON" if entry["new_value"] else "OFF"
        lines.append(f"{entry['timestamp']} - {entry['actor']} turned it {state}")
    await update.effective_message.reply_text("Recent toggle history:\n" + "\n".join(lines))


async def whitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_admin(update, context):
        return
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        await update.effective_message.reply_text(
            "Usage:\n/whitelist add example.com\n/whitelist remove example.com\n/whitelist list"
        )
        return
    action = args[0].lower()
    if action == "list":
        domains = storage.get_settings(chat_id)["whitelist"]
        if not domains:
            await update.effective_message.reply_text("No whitelisted domains yet.")
        else:
            await update.effective_message.reply_text("Whitelisted domains:\n" + "\n".join(domains))
        return
    if action in ("add", "remove") and len(args) >= 2:
        domain = args[1].lower().strip()
        if action == "add":
            storage.add_whitelist_domain(chat_id, domain)
            await update.effective_message.reply_text(f"Added '{domain}' to the whitelist.")
        else:
            storage.remove_whitelist_domain(chat_id, domain)
            await update.effective_message.reply_text(f"Removed '{domain}' from the whitelist.")
        return
    await update.effective_message.reply_text(
        "Usage:\n/whitelist add example.com\n/whitelist remove example.com\n/whitelist list"
    )


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set. Create a .env file with BOT_TOKEN=your_token_here")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("toggle", toggle))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("whitelist", whitelist))
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, moderate))
    logger.info("Bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
