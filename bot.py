import logging
import random
import re
from datetime import time
from typing import Dict, Tuple, Callable, Any

import yaml
from telegram import Update, InlineKeyboardButton, Bot, Message, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import CommandHandler, CallbackContext, Job, CallbackQueryHandler
from telegram.utils.promise import Promise

import restapiservice
import messages
from shared import updater, dispatcher
from utils import send_async, command_handler, edit_async, query_handler

logging.basicConfig(level=logging.INFO)
ADMIN_CHAT_ID = 450786643

PAGE_SIZE = 5

subscriptions: Dict[int, Tuple[Job, str]] = {}
subscriptions_file = 'subscriptions.yml'


def load_subscriptions():
    with open(subscriptions_file) as file:
        subs = yaml.safe_load(file)
    if not subs:
        return
    for chat_id, raw_time in subs.items():
        hour, minute = [int(x) for x in raw_time.split(':')]
        job = updater.job_queue.run_daily(callback=send_quote_of_the_day_to_chat(chat_id),
                                          time=time(hour=hour,
                                                    minute=minute))
        subscriptions[chat_id] = job, raw_time


def save_subscriptions():
    subs = {}
    for chat_id in subscriptions:
        subs[chat_id] = subscriptions[chat_id][1]
    with open(subscriptions_file, mode='w') as file:
        yaml.safe_dump(subs, file)


def send_quote_of_the_day(chat_id: int, context: CallbackContext):
    message_async: Promise = send_async(bot=context.bot,
                                        chat_id=chat_id,
                                        text=messages.LOADING)

    quote = restapiservice.get_quote_of_the_day()

    message: Message = message_async.result()
    del message_async
    edit_async(text=messages.QUOTE_OF_THE_DAY(quote),
               bot=context.bot,
               chat_id=chat_id,
               message_id=message.message_id,
               disable_web_page_preview=True)


def send_quote_of_the_day_to_chat(chat_id: int) -> Callable[[CallbackContext], None]:
    def fun(ctxt: CallbackContext):
        send_quote_of_the_day(chat_id, ctxt)

    return fun


@command_handler
def quotes_handler(update: Update, context: CallbackContext):
    message_async: Promise = send_async(bot=context.bot,
                                        chat_id=update.message.chat_id,
                                        text=messages.LOADING)

    count = restapiservice.get_quotes_count(context.args)
    pages = int((count + PAGE_SIZE - 1) / PAGE_SIZE)

    message: Message = message_async.result()
    edit_async(text=messages.QUOTES_FOUND(count),
               bot=context.bot,
               chat_id=update.message.chat_id,
               message_id=message.message_id)

    if count > 0:
        message_async: Promise = send_async(bot=context.bot,
                                            chat_id=update.message.chat_id,
                                            text=messages.LOADING)

        quotes = restapiservice.get_quotes(context.args, 1, PAGE_SIZE)

        markup = None
        if pages > 1:
            keyboard = [[InlineKeyboardButton(text="next",
                                              callback_data=f'Q2;{pages}'),
                         InlineKeyboardButton(text="last",
                                              callback_data=f'Q{pages};{pages}')]]

            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

        message: Message = message_async.result()
        del message_async

        edit_async(text=messages.QUOTES(quotes),
                   bot=context.bot,
                   chat_id=update.message.chat_id,
                   message_id=message.message_id,
                   reply_markup=markup)


@command_handler
def quote_of_the_day_handler(update: Update, context: CallbackContext):
    send_quote_of_the_day(chat_id=update.message.chat_id,
                          context=context)


@command_handler
def subscribe_handler(update: Update, context: CallbackContext):
    if len(context.args) != 1:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.NO_TIME_ARGUMENT)
        return

    raw_time = context.args[0]
    user_id = update.message.from_user.id

    if user_id in subscriptions and raw_time == subscriptions[user_id][1]:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.ALREADY_SUBSCRIBED(raw_time))
        return

    if not re.match(r'^\d\d:\d\d$', raw_time):
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.INCORRECT_TIME_FORMAT)
        return
    hour, minute = [int(x) for x in raw_time.split(':')]

    if hour > 23:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.INVALID_HOUR)
        return

    if minute > 59:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.INVALID_MINUTE)
        return

    if user_id in subscriptions:
        job, sub_time = subscriptions[user_id]
        job.schedule_removal()

        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.SUBSCRIPTION_REMOVED(sub_time))

    job = context.job_queue.run_daily(callback=send_quote_of_the_day_to_chat(update.message.chat_id),
                                      time=time(hour=hour,
                                                minute=minute))
    subscriptions[user_id] = job, raw_time
    save_subscriptions()

    send_async(bot=context.bot,
               chat_id=update.message.chat_id,
               text=messages.SUBSCRIPTION_SUCCESSFUL(raw_time))


@command_handler
def unsubscribe_handler(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id not in subscriptions:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=messages.NOT_SUBSCRIBED)
        return

    job, sub_time = subscriptions[user_id]
    job.schedule_removal()
    subscriptions.pop(user_id)
    save_subscriptions()
    send_async(bot=context.bot,
               chat_id=update.message.chat_id,
               text=messages.SUBSCRIPTION_REMOVED(sub_time))


@command_handler
def random_handler(update: Update, context: CallbackContext):
    quote = restapiservice.get_quote_random(context.args)
    send_async(bot=context.bot,
               chat_id=update.message.chat_id,
               text=str(quote))


@command_handler
def help_handler(update: Update, context: CallbackContext) -> None:
    send_async(bot=context.bot,
               chat_id=update.message.chat_id,
               text=messages.HELP)


@query_handler
def quotes_page_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query

    edit_async(text=messages.LOADING,
               bot=context.bot,
               chat_id=query.message.chat_id,
               message_id=query.message.message_id,
               reply_markup=None)

    page = int(query.data[1])
    pages = int(query.data[3])

    quotes = restapiservice.get_quotes(context.args, page, PAGE_SIZE)

    buttons = []
    if page > 1:
        buttons.extend([InlineKeyboardButton(text="first",
                                             callback_data=f'Q1;{pages}'),
                       InlineKeyboardButton(text="previous",
                                            callback_data=f'Q{page - 1};{pages}')])

    if page < pages:
        buttons.extend([InlineKeyboardButton(text="next",
                                             callback_data=f'Q{page + 1};{pages}'),
                        InlineKeyboardButton(text="last",
                                             callback_data=f'Q{pages};{pages}')])

    keyboard = [buttons]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    edit_async(text=messages.QUOTES(quotes),
               bot=context.bot,
               chat_id=query.message.chat_id,
               message_id=query.message.message_id,
               reply_markup=markup)


@query_handler
def person_handler(update: Update, context: CallbackContext) -> None:
    pass


def error_handler(update: Update, context: CallbackContext) -> None:
    code = random.randint(1000, 10000)
    logging.error(f"\nError code: {code}")
    if update.message:
        request = update.message.text
        username = update.message.from_user.name
        send_async(bot=context.bot,
                   chat_id=ADMIN_CHAT_ID,
                   text=f"An error occurred for request {request} by user {username}.\n"
                        f"Code: {code}")
        logging.error(f"Request: {request} by user {username}")
    if update.callback_query:
        query: CallbackQuery = update.callback_query
        data = query.data
        username = query.from_user.username
        send_async(bot=context.bot,
                   chat_id=ADMIN_CHAT_ID,
                   text=f"An error occurred for query {data} by user {username}.\n"
                        f"Code: {code}")
        logging.error(f"Query: {data} by user {username}")

    logging.exception(context.error)
    logging.error(f"End of error: {code}")


if __name__ == '__main__':
    load_subscriptions()
    dispatcher.add_handler(CommandHandler('quotes', quotes_handler))
    dispatcher.add_handler(CommandHandler('quoteoftheday', quote_of_the_day_handler))
    dispatcher.add_handler(CommandHandler('subscribe', subscribe_handler))
    dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe_handler))
    dispatcher.add_handler(CommandHandler('random', random_handler))
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback=quotes_page_handler,
                                                pattern=r'^Q'))
    dispatcher.add_handler(CallbackQueryHandler(callback=person_handler,
                                                pattern=r'^P'))
    dispatcher.add_error_handler(error_handler)
    updater.start_polling()
    updater.idle()
