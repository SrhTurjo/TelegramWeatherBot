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
LOCATION, CONFIRM, FORECAST = range(3)

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
    await update.message.reply_text(
        f"Searching Location: {location}"
    )
    source.search_for_locations()

    if source.names is None and source.coordinates is None:
        await update.message.reply_text(
            f"No location found. Please try naming the location differntly."
        )
        return LOCATION
    
    context.user_data['names'] = source.names
    context.user_data['coordinates'] = source.coordinates

    keyboard = []
    
    for i, name in enumerate(source.names):
        keyboard.append([InlineKeyboardButton(name, callback_data=i)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Choose the location you meant",
        reply_markup=reply_markup
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
    await query.edit_message_text(text=f"Getting weather data of {context.user_data['location_name']}")
    
    context.job_queue.run_once(forecast, 0, {
        'chat_id': update.effective_chat.id,
        'data': {
            'location_name': context.user_data['location_name'],
            'location_coordinates': context.user_data['location_coordinates']
        }
    })

async def forecast(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Get the weather data and send it to the user."""

    chat_id = context.job.data['chat_id']
    data = context.job.data['data']
    location_name = data['location_name']
    location_coordinates = data['location_coordinates']


    # Get the weather data for the selected location
    app = WeatherApp()
    app.get_weather(location_coordinates)
    today = app.today
    weather_report = "Today's weather: \n"
    for data in today:
        weather_report += f"{data['time']}: {data['weather']} {data['temp']}°C\n"


    # Send the weather data to the user
    await context.bot.send_message(chat_id, f"The weather in {location_name} is: {weather_report}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """End Conversation by command."""
    user = update.effective_user
    await update.message.reply_text(
        f"Bye! I hope we can talk again some day.",
        reply_markup= markup_keyboard
    )

    return ConversationHandler.END

if __name__ == '__main__':
    application = ApplicationBuilder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LOCATION: [MessageHandler(filters.TEXT & (~filters.COMMAND) , get_location_name)],
            CONFIRM: [CallbackQueryHandler(confirm_location_button)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()