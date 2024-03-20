import os 
token = os.environ.get('TELE_TOKEN')

import logging
# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



from telegram import Update, ForceReply, ReplyKeyboardMarkup , InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import (
    MessageHandler, CommandHandler, 
    ContextTypes, 
    filters,
    ApplicationBuilder
    )

markup_keyboard = ReplyKeyboardMarkup([['/start','']], is_persistent=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    msg = "I'm a weather bot, give me a location. I'll tell the weather there!"


    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}. {msg}",
        reply_markup= markup_keyboard
    )

    await update.message.reply_text(
        f"What is the location?",
        reply_markup= ForceReply(selective=True, input_field_placeholder="Reply your location")
    )

async def get_location_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    reply = update.message.reply_to_message
    if reply.text == "What is the location?":
        location = update.message.text
        await update.message.reply_text(
            f"Location: {location}",
            reply_markup=markup_keyboard
        )
                                        


if __name__ == '__main__':

    application = ApplicationBuilder().token(token).build()

    start_handler = CommandHandler('start', start)
    location_handler = MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.REPLY, get_location_name)

    application.add_handler(start_handler)
    application.add_handler(location_handler)

    application.run_polling()