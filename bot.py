"""
Runs the server in polling mode.
"""

from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from free_rooms.bot import free_rooms, button, handle_user_response


with open(".token", "r") as f:
    BOT_TOKEN = f.read()


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("free_rooms", free_rooms))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_response))  # Add a handler for text messages
app.run_polling()