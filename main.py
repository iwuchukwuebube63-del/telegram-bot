from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Replace this with your actual bot token
import os
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Your admin username and group link
ADMIN_USERNAME = "@Danzy_101"
GROUP_LINK = "https://t.me/+gMeI-26g9bNkNzI0"

# Store activated users (in memory)
activated_users = set()

# Dummy activation codes (you can replace this with a real system)
valid_codes = {"123456", "654321", "botaccess"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Welcome, {user.first_name}!\n\nTo activate this bot, please get your one-time code from the admin: {ADMIN_USERNAME}\nOnce you have it, send it here to continue."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    if user_id in activated_users:
        await update.message.reply_text("✅ You're already activated.")
        return

    if text in valid_codes:
        activated_users.add(user_id)
        await update.message.reply_text(
            f"✅ Activation successful!\nYou're now verified to use this bot.\n\n🎉 Join our group here: {GROUP_LINK}"
        )
    else:
        await update.message.reply_text("❌ Invalid activation code. Please contact the admin for a valid one.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
