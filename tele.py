import os 
from weather import WeatherApp
token = os.environ.get('TELE_TOKEN')


import logging
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



from telegram import Update, ReplyKeyboardMarkup , InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from telegram.ext import (
    MessageHandler, CommandHandler, ConversationHandler, CallbackQueryHandler,
    ContextTypes, 
    filters,
    ApplicationBuilder
    )

markup_keyboard = ReplyKeyboardMarkup([['/start','']], is_persistent=True)
LOCATION, CONFIRM, UNIT_SWAP = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    msg = "I'm a weather bot, give me a location. I'll tell the weather there!"


    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}. {msg} Type your location.",
        reply_markup= markup_keyboard
    )
    return LOCATION

async def get_location_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    source = WeatherApp()
    location = update.message.text
    source.search = location
    msg = await update.message.reply_text(
        f"Searching Location: {location}"
    )
    source.search_for_locations()

    if source.names is None and source.coordinates is None:
        await msg.edit_text(
            f"No location found. Please try naming the location differntly."
        )
        return LOCATION
    
    context.user_data['names'] = source.names
    context.user_data['coordinates'] = source.coordinates

    keyboard = []
    
    for i, name in enumerate(source.names):
        keyboard.append([InlineKeyboardButton(name, callback_data=i)])

    markup = InlineKeyboardMarkup(keyboard)
    
    await msg.edit_text(
        f"Choose the location you meant",
        reply_markup= markup
    )
    return CONFIRM


async def confirm_location_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    """Handle button presses."""
    query = update.callback_query
    await query.answer()

    # The callback_data is available in query.data
    selected_location = query.data

    # Do something with the selected location
    context.user_data['location_name'] = context.user_data['names'][int(selected_location)]
    context.user_data['location_coordinates'] = context.user_data['coordinates'][int(selected_location)]

    markup = InlineKeyboardMarkup([[InlineKeyboardButton("Show in Celcius", callback_data='C')]])
    msg = forecast(context)

    await query.edit_message_text(
        text=msg,
        reply_markup= markup)
    
    return UNIT_SWAP


def forecast(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the weather data and send it to the user."""

    location_name = context.user_data['location_name']
    location_coordinates = context.user_data['location_coordinates']


    # Get the weather data for the selected location
    app = WeatherApp()
    app.get_weather(location_coordinates, unit = "imperial")
    today = app.today
    context.user_data['weather'] = today
    weather_report = f"Today's weather in {location_name}:\n"
    for data in today:
        weather_report += f"{data['time']}: {data['weather']} {data['temp']}°F\n"

    return weather_report


async def unit_swap_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    
        """Handle button presses."""
        query = update.callback_query
        await query.answer()
    
        # The callback_data is available in query.data
        selected_unit = query.data

        location_name = context.user_data['location_name']
    
        # Do something with the selected location
        today = context.user_data['weather']


        weather_report = f"Today's weather in {location_name}:\n"

        if selected_unit == 'C':
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("Show in Farenheit", callback_data='F')]])
            for data in today:
                weather_report += f"{data['time']}: {data['weather']} {round((5/9)*(data['temp']-32), 2)}°C\n"
        else:
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("Show in Celcius", callback_data='C')]])
            for data in today:
                weather_report += f"{data['time']}: {data['weather']} {data['temp']}°F\n" 

        await query.edit_message_text(
            text=f"{weather_report}",
            reply_markup= markup)

        return UNIT_SWAP


if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND) , get_location_name)],
            UNIT_SWAP: [CallbackQueryHandler(unit_swap_button, pattern="^(C|F)$")],
            CONFIRM: [CallbackQueryHandler(confirm_location_button, pattern="^(\d+)$")],
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()