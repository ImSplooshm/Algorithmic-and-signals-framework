from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

async def print_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        forward_origin = update.message.forward_origin

        if forward_origin and hasattr(forward_origin, "chat"):
            chat = forward_origin.chat
            await update.message.reply_text(f"Channel chat ID: {chat.id}\nTitle: {chat.title}")
            print(f"Channel chat ID: {chat.id} | Title: {chat.title}")
        else:
            await update.message.reply_text("Forwarded message does not include channel info.")
            print("No channel info found in forward_origin.")
    else:
        print("Update did not contain a message.")

app = ApplicationBuilder().token("7768585506:AAFLbbmcIu8Z2JXZ5dzoH1QuVvEeRJBBK5A").build()
app.add_handler(MessageHandler(filters.ALL, print_chat_id))
app.run_polling()
