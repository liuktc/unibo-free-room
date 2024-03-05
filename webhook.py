import os
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from free_rooms.bot import free_rooms, button, handle_user_response


BOT_TOKEN = os.environ.get("TOKEN")
if BOT_TOKEN is None:
    with open(".token", "r") as f:
        BOT_TOKEN = f.read()

app = FastAPI()

ptb = ApplicationBuilder().token(BOT_TOKEN).build()
ptb.add_handler(CommandHandler("free_rooms", free_rooms))
ptb.add_handler(CallbackQueryHandler(button))
ptb.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_response))


class TelegramWebhook(BaseModel):
    update_id: int
    message: Optional[dict]
    edited_message: Optional[dict]
    channel_post: Optional[dict]
    edited_channel_post: Optional[dict]
    inline_query: Optional[dict]
    chosen_inline_result: Optional[dict]
    callback_query: Optional[dict]
    shipping_query: Optional[dict]
    pre_checkout_query: Optional[dict]
    poll: Optional[dict]
    poll_answer: Optional[dict]


@app.post("/webhook")
async def webhook(webhook_data: TelegramWebhook):
    await ptb.initialize()
    await ptb.process_update( Update.de_json(webhook_data.__dict__, ptb.bot) )
    await ptb.shutdown()

    return {"message": "ok"}


@app.get("/")
def index():
    return {"message": "I'm working, probably"}
