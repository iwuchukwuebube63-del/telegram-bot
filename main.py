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
GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))      # e.g. -1001234567890
ADMIN_ID = 7592357527                               # your Telegram ID
ADMIN_USERNAME = "Danzy_101"                        # without the "@"
DATA_FILE = "activated_users.json"

# ------------- Persistence Helpers -------------
def load_activated_users():
    try:
        with open(DATA_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_activated_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(list(users), f)

activated_users = load_activated_users()
valid_codes = set()

# ------------- Utility Functions -------------
def is_admin(user):
    return (
        user.id == ADMIN_ID
        or (user.username and user.username.lower() == ADMIN_USERNAME.lower())
    )

# ------------- Command Handlers -------------
from datetime import datetime, timedelta

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"[DEBUG] /start called by {user.id}")

    if user.id in activated_users:
        expire_time = datetime.utcnow() + timedelta(seconds=10)
        try:
            link = await context.bot.create_chat_invite_link(
                chat_id=GROUP_ID,
                member_limit=1,
                expire_date=expire_time
            )
            await update.message.reply_text(
                f"✅ You’re already activated!\n🔗 One-time link (valid for 10 seconds):\n{link.invite_link}"
            )
        except Exception as e:
            print(f"[ERROR] /start link failed for {user.id}: {e}")
            await update.message.reply_text(f"❌ Failed to generate link: {e}")
    else:
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! Ask @{ADMIN_USERNAME} for an activation code, then send it here."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in activated_users:
        text = (
            "🛠 Commands for activated users:\n"
            "/start     – get a one-time link\n"
            "/getlink   – get a fresh one-time link\n"
            "/myid      – show your user ID\n"
            "/help      – show this message\n\n"
            "👑 Admin commands:\n"
            "/generate   – create an activation code\n"
            "/list_users – list all activated users\n"
            "/revoke     – revoke a user’s access\n"
            "/broadcast  – send message to all activated users"
        )
    else:
        text = (
            "🔑 You need activation to use commands.\n"
            f"Ask @{ADMIN_USERNAME} for a one-time code, then send it here."
        )
    await update.message.reply_text(text)

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(f"🆔 Your user ID is {user.id}")

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"[DEBUG] /generate called by {user.id} (@{user.username})")
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
    code = str(random.randint(100000, 999999))
    valid_codes.add(code)
    await update.message.reply_text(f"✅ Your activation code is: {code}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text.strip()

    if user.id in activated_users:
        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, member_limit=1
        )
        return await update.message.reply_text(
            f"✅ Here’s a fresh one-time link:\n{link.invite_link}"
        )

    if text in valid_codes:
        valid_codes.remove(text)
        activated_users.add(user.id)
        save_activated_users(activated_users)
        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID, member_limit=1
        )
        return await update.message.reply_text(
            "✅ Activation successful!\n"
            f"🎉 Here’s your one-time group link:\n{link.invite_link}"
        )

    await update.message.reply_text("❌ Invalid code. Please ask the admin for a valid one.")

from datetime import datetime, timedelta

async def getlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"[DEBUG] /getlink called by {user.id}")

    if user.id not in activated_users:
        return await update.message.reply_text("❌ You’re not activated. Use /start first.")

    expire_time = datetime.utcnow() + timedelta(seconds=10)
    try:
        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,
            expire_date=expire_time
        )
        await update.message.reply_text(
            f"🔗 Your one-time link (valid for 10 seconds):\n{link.invite_link}"
        )
    except Exception as e:
        print(f"[ERROR] getlink failed for {user.id}: {e}")
        await update.message.reply_text(f"❌ Failed to generate link: {e}")
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
    if not activated_users:
        return await update.message.reply_text("No users have been activated yet.")
    lines = ["🧑‍💻 Activated users:"]
    lines += [f"– {uid}" for uid in activated_users]
    await update.message.reply_text("\n".join(lines))

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
    if not context.args:
        return await update.message.reply_text("Usage: /revoke <user_id>")
    try:
        target_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Invalid user ID.")
    if target_id in activated_users:
        activated_users.remove(target_id)
        save_activated_users(activated_users)
        await update.message.reply_text(f"✅ Revoked access for user {target_id}.")
    else:
        await update.message.reply_text("❌ That user is not activated.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
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
    port = int(os.getenv("PORT", 10000))
    HTTPServer(("0.0.0.0", port), DummyHandler).serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# ------------- Bot Startup -------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("generate", generate_code))
    app.add_handler(CommandHandler("getlink", getlink))
    app.add_handler(CommandHandler("list_users", list_users))
    app.add_handler(CommandHandler("revoke", revoke_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
