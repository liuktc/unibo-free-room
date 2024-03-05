from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from finder import searchFreeRooms

with open(".token", "r") as f:
    BOT_TOKEN = f.read()

async def free_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Today", callback_data="today"),
        InlineKeyboardButton("Another Day", callback_data="another_day")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('What date do you want to search?', reply_markup=reply_markup)
    context.user_data['state'] = 'awaiting_date' 
    #print(context)
    #print(update)
    """
    user_message = update.message.text
    args = user_message.split(" ")[1:]
    print(args)
    start_time = args[0]
    end_time = args[1]

    res = searchFreeRooms(start_time, end_time) 
    await update.message.reply_text(f'This rooms are empty {res}', reply_markup=reply_markup)
    """
    

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    print(f'Query={query.data}')
    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    # print(update)
    # print(update.message)
    if query.data == "today":
        await query.edit_message_reply_markup(None)
        await query.edit_message_text("Insert the time slots in the format hh:mm hh:mm\nExample: 8:00 12:00", reply_markup=None)
        context.user_data['state'] = 'awaiting_time_slots'
        context.user_data['date'] = 'today'
    elif query.data == "another_day":
        await query.edit_message_reply_markup(None)
        await query.edit_message_text("Insert the date in the format dd/mm/yyyy\nExample: 23/04/2024", reply_markup=None)
        context.user_data['state'] = 'awaiting_date'
    else:
        print("Unknown action")
    # await query.edit_message_text(text=f"Selected option: {query.data}")

async def handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'state' in context.user_data:
        if context.user_data['state'] == 'awaiting_date':
            user_date = update.message.text
            context.user_data['date'] = user_date 
            await update.message.reply_text("Thank you! Now, insert the time slots in the format hh:mm hh:mm\nExample: 8:00 12:00")
            context.user_data['state'] = 'awaiting_time_slots'

        elif context.user_data['state'] == 'awaiting_time_slots':
            user_time_slots = update.message.text
            context.user_data['time_slots'] = user_time_slots

            # API Call with retrieved data 
            start_time, end_time = user_time_slots.split() # Assuming you get these from the input
            if context.user_data['date'] == 'today':
                search_result = searchFreeRooms(start_time, end_time) 
            else:
                day, month, year = context.user_data['date'].split("/")
                search_result = searchFreeRooms(start_time, end_time,day=int(day), month=int(month), year=int(year) )

            text = ""
            for room in search_result:
                text += room.name + "\n"
            await update.message.reply_text(text)

            # Reset state
            del context.user_data['state'] 



app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("free_rooms", free_rooms))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_response))  # Add a handler for text messages
app.run_polling()