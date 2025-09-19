import os
import json
import random
import threading
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ─── Configuration ──────────────────────────────────────────────────────────────
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))
ADMIN_ID = 7592357527
ADMIN_USERNAME = "Danzy_101"
DATA_FILE = "activated_users.json"

# ─── Persistence ────────────────────────────────────────────────────────────────
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

# ─── Utility ────────────────────────────────────────────────────────────────────
def is_admin(user):
    return (
        user.id == ADMIN_ID
        or (user.username and user.username.lower() == ADMIN_USERNAME.lower())
    )

# ─── Command Handlers ───────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return

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
            await update.message.reply_text(f"❌ Failed to generate link: {e}")
    else:
        await update.message.reply_text(
            f"👋 Hi {user.first_name}! Ask @{ADMIN_USERNAME} for an activation code, then send it here."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.effective_chat.type != "private":
        return

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
    if update.effective_chat.type != "private":
        return
    user_id = update.effective_user.id
    await update.message.reply_text(f"🆔 Your user ID is: {user_id}")

async def getlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user = update.effective_user
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
        await update.message.reply_text(f"❌ Failed to generate link: {e}")

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user = update.effective_user
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
    code = str(random.randint(100000, 999999))
    valid_codes.add(code)
    await update.message.reply_text(f"✅ Your activation code is: {code}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user = update.effective_user
    text = update.message.text.strip()

    if user.id in activated_users:
        expire_time = datetime.utcnow() + timedelta(seconds=10)
        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,
            expire_date=expire_time
        )
        return await update.message.reply_text(
            f"🔗 You're already activated!\nOne-time link (valid 10s):\n{link.invite_link}"
        )

    if text in valid_codes:
        valid_codes.remove(text)
        activated_users.add(user.id)
        save_activated_users(activated_users)

        expire_time = datetime.utcnow() + timedelta(seconds=10)
        link = await context.bot.create_chat_invite_link(
            chat_id=GROUP_ID,
            member_limit=1,
            expire_date=expire_time
        )
        return await update.message.reply_text(
            "✅ Activation successful!\n"
            f"🎉 Here's your one-time group link (valid 10s):\n{link.invite_link}"
        )

    await update.message.reply_text("❌ Invalid code. Please ask the admin for a valid one.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user = update.effective_user
    if not is_admin(user):
        return await update.message.reply_text("❌ You’re not authorized.")
    if not activated_users:
        return await update.message.reply_text("No users have been activated yet.")
    lines = ["🧑‍💻 Activated users:"]
    lines += [f"– {uid}" for uid in activated_users]
    await update.message.reply_text("\n".join(lines))

async def revoke_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
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
    if update.effective_chat.type != "private":
        return
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
    sent = len(activated_users) -[43dcd9a7-70db-4a1f-b0ae-981daa162054](https://github.com/Yeroc64444331123699963/yeroc_pcjs/tree/8490a15879d3ac82e08fcd067676e3941f322d5d/documents%2Fbooks%2Fmspl13%2Fmsdos%2Fencyclopedia%2Fappendix-a%2Findex.md?citationMarker=43dcd9a7-70db-4a1f-b0ae-981daa162054 "1")[43dcd9a7-70db-4a1f-b0ae-981daa162054](https://github.com/ngtaloc/TotNghiep-Project/tree/8b72be93496d37f227ac7d87d5aae25d5241d519/WebEng%2FWebEng%2FContent%2FTemplate%2Fplugins%2Fraphael%2Fraphael.js?citationMarker=43dcd9a7-70db-4a1f-b0ae-981daa162054 "2")[43dcd9a7-70db-4a1f-b0ae-981daa162054](https://github.com/aurelien-castel/DUT-Oct-2019-API-IA/tree/50bdb4267f4678a77435b151d3bae2e1a1aa1903/projet%2Fagents%2Foptimisation_MinMax%2Ftree%2Fminimax_tree.py?citationMarker=43dcd9a7-70db-4a1f-b0ae-981daa162054 "3")[43dcd9a7-70db-4a1f-b0ae-981daa162054](https://github.com/sensu/sensu-docs/tree/3f9b0c72df4d494de6cf04803ec229e3a89c6ec3/content%2Fsensu-go%2F6.5%2Fobservability-pipeline%2Fobserve-entities%2Fmonitor-external-resources.md?citationMarker=43dcd9a7-70db-4a1f-b0ae-981daa162054 "4")
