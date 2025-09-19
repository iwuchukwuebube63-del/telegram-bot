from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random, string

ADMIN_ID = 7592357527
one_time_codes = set()
authorized_users = set()

async def generate_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ You're not authorized to generate codes.")
        return

    new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    one_time_codes.add(new_code)
    await update.message.reply_text(f"🔑 New one-time code: {new_code}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in authorized_users:
        await update.message.reply_text("✅ You're already activated.")
    else:
        await update.message.reply_text("🔐 Please enter your one-time access code:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in authorized_users:
        await update.message.reply_text(f"You said: {text}")
    elif text in one_time_codes:
        authorized_users.add(user_id)
        one_time_codes.remove(text)
        await update.message.reply_text("✅ Activation successful! You can now use the bot.")
    else:
        await update.message.reply_text("❌ Invalid or already used code.")

if __name__ == "__main__":
    app = ApplicationBuilder().token("8403474618:AAFwBgzW1ZXx9NTQlF5g0s8VEzPHv1aXzyQ").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate", generate_code))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
