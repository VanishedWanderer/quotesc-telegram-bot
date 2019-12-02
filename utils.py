import logging
from typing import Union, Callable

from telegram import Bot, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

import messages


def command_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext):
        try:
            logging.info(f"Request {update.message.text} by {update.message.from_user.username}")
            handler(update, context)
        except Exception as err:
            send_async(bot=context.bot,
                       chat_id=update.message.chat_id,
                       text=messages.ERROR_OCCURRED)
            raise err

    return func


def query_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext):
        try:
            logging.info(f"Query {update.callback_query.data} by {update.callback_query.from_user.username}")
            handler(update, context)
        except Exception as err:
            send_async(bot=context.bot,
                       chat_id=update.callback_query.message.chat_id,
                       text=messages.ERROR_OCCURRED)
            raise err

    return func


@run_async
def send_async(bot: Bot,
               chat_id: Union[int, str],
               text: str,
               disable_web_page_preview: bool = True,
               reply_to_message_id: int = None,
               reply_markup: InlineKeyboardMarkup = None):
    return bot.sendMessage(chat_id=chat_id,
                           text=text,
                           display_web_page_preview=disable_web_page_preview,
                           reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup)


@run_async
def edit_async(text: str,
               bot: Bot,
               chat_id: Union[int, str],
               message_id: int,
               disable_web_page_preview: bool = None,
               reply_markup: InlineKeyboardMarkup = None):
    return bot.editMessageText(text=text,
                               chat_id=chat_id,
                               message_id=message_id,
                               display_web_page_preview=disable_web_page_preview,
                               reply_markup=reply_markup)


def read_token():
    with open('token.txt') as token_file:
        return token_file.readline()
