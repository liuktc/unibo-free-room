import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from .finder import planFreeRooms, BUILDINGS
import re


QUERY_DATE_PROMPT = (
    "Insert the date in the format:\n"
    "<code>dd/mm/yyyy</code>\n"
    "Example: <code>23/04/2024</code>"

)
QUERY_TIME_PROMPT = (
    "Insert the time slots in the format:\n"
    "<code>hh:mm hh:mm [comma separated buildings] \"[comma sep. excluded rooms]\"</code>\n"
    "Examples:\n"
    "<code>8:00 12:00</code>\n"
    "<code>8:00 12:00 eng</code>\n"
    "<code>8:00 12:00 eng,chem</code>\n"
    "<code>8:00 12:00 eng,chem \"AULA 0.1, AULA 0.2\"</code>\n"
    f"\nAvailable buildings are: {', '.join([f'<code>{b}</code>' for b in BUILDINGS])}"
)


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
        await query.edit_message_text(QUERY_TIME_PROMPT, reply_markup=None, parse_mode=telegram.constants.ParseMode.HTML)
        context.user_data['state'] = 'awaiting_time_slots'
        context.user_data['date'] = 'today'
    elif query.data == "another_day":
        await query.edit_message_reply_markup(None)
        await query.edit_message_text(QUERY_DATE_PROMPT, reply_markup=None, parse_mode=telegram.constants.ParseMode.HTML)
        context.user_data['state'] = 'awaiting_date'
    else:
        print("Unknown action")
    # await query.edit_message_text(text=f"Selected option: {query.data}")


def __parseInput(input, state):
    if state == "awaiting_time_slots":
        pattern = re.compile(r"[^\s\"']+|\"([^\"]*)\"|'([^']*)'")
        args = [None] * 4
        i = 0

        match = pattern.search(input)
        while match is not None:
            input = input[:match.span()[0]] + input[match.span()[1]:]
            args[i] = match.group()

            match = pattern.search(input)
            i += 1

        if args[2] is not None: args[2] = args[2].lower().split(",")
        if args[3] is not None: args[3] = [s.strip() for s in args[3][1:-1].split(",")]

        return args
    else:
        return input


async def handle_user_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if 'state' in context.user_data:
        if context.user_data['state'] == 'awaiting_date':
            user_date = update.message.text
            context.user_data['date'] = user_date 
            await update.message.reply_text(f"Thank you! Now, {QUERY_TIME_PROMPT[0].lower()}{QUERY_TIME_PROMPT[1:]}", parse_mode=telegram.constants.ParseMode.HTML)
            context.user_data['state'] = 'awaiting_time_slots'

        elif context.user_data['state'] == 'awaiting_time_slots':
            user_input = update.message.text
            user_input_args = __parseInput(user_input, "awaiting_time_slots")
            # context.user_data['time_slots'] = user_time_slots

            # API Call with retrieved data 
            start_time, end_time = user_input_args[0], user_input_args[1]
            buildings_filter = user_input_args[2]
            exclude_rooms = user_input_args[3]
            if context.user_data['date'] == 'today':
                search_result = planFreeRooms(start_time, end_time, buildings_filter=buildings_filter, exclude_rooms=exclude_rooms) 
            else:
                day, month, year = context.user_data['date'].split("/")
                search_result = planFreeRooms(start_time, end_time, day=int(day), month=int(month), year=int(year), buildings_filter=buildings_filter, exclude_rooms=exclude_rooms)

            text = ""
            if len(search_result) == 0:
                text = "No free rooms"
            else:
                for plan in search_result:
                    text += f"<b>>>>>> {plan['slot']} >>>>></b>"

                    prev_building = None
                    for room in plan["rooms"]:
                        if prev_building != room.building:
                            prev_building = room.building
                            if len(text) != 0: text += "\n"
                            text += f"<b>--- {room.building.upper()} ---</b>\n"
                        text += room.name + "\n"

                    text += f"\n"

            await update.message.reply_text(text, parse_mode=telegram.constants.ParseMode.HTML)

            # Reset state
            del context.user_data['state'] 