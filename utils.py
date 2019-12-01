from typing import Union, Callable, Dict, Tuple

from telegram import Bot, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, Job
from telegram.ext.dispatcher import run_async

import messages


def command_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:

    def func(update: Update, context: CallbackContext):
        try:
            handler(update, context)
        except Exception as err:
            send_async(bot=context.bot,
                       chat_id=update.message.chat_id,
                       text=messages.ERROR_OCCURRED)
            raise err

    return func


@run_async
def send_async(bot: Bot,
               chat_id: Union[int, str],
               text: str,
               disable_web_page_preview: bool = None,
               reply_to_message_id: int = None,
               reply_markup: InlineKeyboardMarkup = None):
    bot.sendMessage(chat_id=chat_id,
                    text=text,
                    display_web_page_preview=disable_web_page_preview,
                    reply_to_message_id=reply_to_message_id,
                    reply_markup=reply_markup)


def read_token():
    with open('token.txt') as token_file:
        return token_file.readline()
