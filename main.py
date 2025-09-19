from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import os
import random

# Bot token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Admin info
ADMIN_ID = 7592357527
ADMIN_USERNAME = "@Danzy_101"
GROUP_LINK = "https://t.me/+gMeI-26g9bNkNzI0"

# In-memory storage
valid_codes = set()
activated_users = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    if user_id in activated_users:
        # Already activated: remind them of the group link
        return await update.message.reply_text(
            f"✅ You’re already activated.\n\n🎉 Join our group here: {GROUP_LINK}"
        )

    # Not yet activated: prompt for code
    await update.message.reply_text(
        f"👋 Hi, {user.first_name}!\n"
        f"To activate this bot, please get your one-time code from the admin: {ADMIN_USERNAME}\n"
        "Once you have it, send it here to continue."
    )


async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != ADMIN_ID:
        return await update.message.reply_text("❌ You’re not authorized to generate codes.")

    # Create and store a six-digit code
    code = str(random.randint(100000, 999999))
    valid_codes.add(code)

    await update.message.reply_text(f"✅ Your one-time activation code is: {code}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    # If they’re already activated, remind them and stop
    if user_id in activated_users:
        return await update.message.reply_text(
            f"✅ You’re already activated.\n\n🎉 Join our group here: {GROUP_LINK}"
        )

    # Check the code
    if text in valid_codes:
        # One-time use: remove it immediately
        valid_codes.remove(text)
        activated_users.add(user_id)

        return await update.message.reply_text(
            "✅ Activation successful!\n"
            "You’re now verified to use this bot.\n\n"
            f"🎉 Join our group here: {GROUP_LINK}"
        )

    # Invalid code
    await update.message.reply_text(
        "❌ Invalid activation code.\n"
        "Please contact the admin for a valid one."
    )


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_code))

    # All text messages go here
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
