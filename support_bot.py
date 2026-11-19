import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # BotFather se mila token
ADMIN_ID = 123456789               # @userinfobot se mili aapki numeric ID

# Logging setup (errors dekhne ke liye)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Dictionary jo store karegi: {admin_chat_message_id: user_chat_id}
message_map = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User jab /start dabaye"""
    user = update.effective_user
    if user.id == ADMIN_ID:
        await update.message.reply_text("👋 Admin mode active! Users ke messages yahan aayenge. Kisi bhi message par Reply karke jawab dein.")
    else:
        await update.message.reply_text(
            f"Namaste {user.first_name}! 👋\n"
            "Apna sawal ya query yahan likhkar bhejein, humari team jald hi reply karegi."
        )

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Member ke message ko Admin ko forward karna"""
    user = update.effective_user
    msg = update.message

    # User info header bhejna taaki pata chale kisne message kiya
    user_info = f"📩 **New Query** from {user.full_name} (`{user.id}`)"
    if user.username:
        user_info += f" | @{user.username}"

    await context.bot.send_message(chat_id=ADMIN_ID, text=user_info, parse_mode="Markdown")

    # Actual message (text/photo/file) ko Admin ke chat mein copy/forward karna
    forwarded_msg = await msg.forward(chat_id=ADMIN_ID)

    # Mapping save karna taaki Admin jab is forwarded_msg par reply kare toh user ID mil sake
    message_map[forwarded_msg.message_id] = user.id

    await msg.reply_text("✅ Aapki query receive ho gayi hai. Reply ka intezar karein.")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin ke reply ko wapas sahi User ko bhejna"""
    msg = update.message

    # Check karein ki Admin ne kisi message par reply kiya hai ya nahi
    if not msg.reply_to_message:
        await msg.reply_text("⚠️ Kisi user ko jawab dene ke liye uske forwarded message par **Reply** karein.")
        return

    replied_msg_id = msg.reply_to_message.message_id
    target_user_id = message_map.get(replied_msg_id)

    if not target_user_id:
        await msg.reply_text("❌ Is message ka user record nahi mila (shayad bot restart hua tha).")
        return

    try:
        # Admin ka text, photo, ya file seedha user ko copy karke bhejna (aapki identity hidden rahegi)
        await msg.copy(chat_id=target_user_id)
        await msg.reply_text("📤 Reply sent!")
    except Exception as e:
        await msg.reply_text(f"❌ Message bhejne mein error aaya (User ne bot block kiya ho sakta hai): {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    
    # Admin ke messages handle karne ke liye
    app.add_handler(MessageHandler(filters.User(user_id=ADMIN_ID) & ~filters.COMMAND, handle_admin_reply))
    
    # Baaki sabhi users ke messages handle karne ke liye
    app.add_handler(MessageHandler(~filters.User(user_id=ADMIN_ID) & ~filters.COMMAND, handle_user_message))

    print("Bot chal raha hai...")
    app.run_polling()

if __name__ == "__main__":
    main()
