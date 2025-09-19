import os
import json
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ------------- Configuration -------------
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = 7592357527
ADMIN_USERNAME = "@Danzy_101"
# Your group’s chat ID (must add the bot as admin in the group)
GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))
ACTIVATED_FILE = "activated_users.json"

# ------------- Persistence Helpers -------------
def load_activated_users():
    try:
        with open(ACTIVATED_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_activated_users(users):
    with open(ACTIVATED_FILE, "w") as f:
        json.dump(list(users), f)

# ------------- In-Memory State -------------
valid_codes = set()
activated_users = load_activated_users()

# ------------- Command Handlers -------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in activated_users:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, member_limit=1
        )
        return await update.message.reply_text(
            f"✅ You’re already activated.\n\n"
            f"🎉 Join our group here: {invite.invite_link}"
        )

    await update.message.reply_text(
        f"👋 Hello, {user.first_name}!\n\n"
        f"To use this bot, get your one-time activation code from the admin: {ADMIN_USERNAME}\n"
        "Once you have it, send it here to activate."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in activated_users:
        help_text = (
            "🛠️ *Commands for Activated Users:*\n\n"
            "/start \\- Check activation status and get a fresh link\n"
            "/help \\- Show this help message\n"
            "/getlink \\- Generate a one\\-time group invite link\n"
            "/generate \\- \\(Admin only\\) Create an activation code\n"
            "/list_users \\- \\(Admin only\\) View activated users\n"
            "/revoke <user_id> \\- \\(Admin only\\) Revoke a user's access\n"
            "/broadcast <message> \\- \\(Admin only\\) Send a message to all activated users"
        )
    else:
        help_text = (
            "👋 *Welcome to the Bot!*\n\n"
            "You need to be activated to use commands.\n"
            f"Get your one-time code from the admin: {ADMIN_USERNAME}\n"
            "Send the code here to unlock access.\n\n"
            "After activation, use /help to see all commands."
        )

    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You’re not authorized to generate codes.")

    code = str(random.randint(100000, 999999))
    valid_codes.add(code)
    await update.message.reply_text(f"✅ Your one-time activation code is: `{code}`", parse_mode="MarkdownV2")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if user.id in activated_users:
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, member_limit=1
        )
        return await update.message.reply_text(
            f"✅ You’re already activated.\n\n"
            f"🎉 Join our group here: {invite.invite_link}"
        )

    if text in valid_codes:
        valid_codes.remove(text)
        activated_users.add(user.id)
        save_activated_users(activated_users)
        invite = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, member_limit=1
        )
        return await update.message.reply_text(
            "✅ Activation successful!\n\n"
            f"🎉 Here’s your one-time group link: {invite.invite_link}"
        )

    await update.message.reply_text(
        "❌ Invalid code. Please contact the admin for a valid activation code."
    )

async def getlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in activated_users:
        return await update.message.reply_text("❌ You’re not activated. Use /start to activate.")

    invite = await context.bot.create_chat_invite_link(
        chat_id=GROUP_ID, member_limit=1
    )
    await update.message.reply_text(f"🎉 Your one-time group link: {invite.invite_link}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You’re not authorized to view users.")

    if not activated_users:
        return await update.message.reply_text("No users have been activated yet.")

    lines = [f"🧑‍💻 Activated Users ({len(activated_users)}):"]
    lines += [f"– `{uid}`" for uid in activated_users]
    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You’re not authorized to revoke users.")

    if not context.args:
        return await update.message.reply_text("Usage: /revoke <user_id>")

    try:
        target = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Invalid user ID format.")

    if target in activated_users:
        activated_users.remove(target)
        save_activated_users(activated_users)
        await update.message.reply_text(f"✅ Revoked access for user `{target}`.", parse_mode="MarkdownV2")
    else:
        await update.message.reply_text("❌ That user is not activated.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You’re not authorized to broadcast.")

    message = " ".join(context.args).strip()
    if not message:
        return await update.message.reply_text("Usage: /broadcast <message>")

    failures = []
    for uid in activated_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 Broadcast:\n{message}")
        except:
            failures.append(uid)

    sent = len(activated_users) - len(failures)
    summary = f"✅ Broadcast sent to {sent} user(s)."
    if failures:
        summary += "\n⚠️ Failed to send to: " + ", ".join(str(x) for x in failures)
    await update.message.reply_text(summary)

# ------------- Dummy HTTP Server for Render -------------
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running.")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ------------- Bot Startup -------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("getlink", getlink))
    app.add_handler(CommandHandler("generate", generate_code))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("revoke", revoke_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
