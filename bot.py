import logging
import random
import re
import threading
from datetime import time
from typing import Dict, Tuple, Callable

import yaml
from telegram import Update, InlineKeyboardButton, Message, InlineKeyboardMarkup, CallbackQuery
from telegram.error import Unauthorized, BadRequest
from telegram.ext import CommandHandler, CallbackContext, Job, CallbackQueryHandler, Updater, MessageHandler, Filters
from telegram.utils.promise import Promise

import messages
import restapiservice
from top_secret import top_secret_text_handler, top_secret_sticker_handler
from utils import send_text_async, command_handler, edit_async, query_handler, send_admins_async, admin_command_handler, \
    whitelist, blacklist, admin_query_handler, remove_markup

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ])

PAGE_SIZE = 5

subscriptions: Dict[int, Tuple[Job, str]] = {}
subscriptions_file = 'subscriptions.yml'
token_file = 'token.txt'


def load_subscriptions() -> None:
    with open(subscriptions_file) as s_file:
        subs = yaml.safe_load(s_file)
    if not subs:
        return
    for chat_id, raw_time in subs.items():
        [hour, minute] = [int(x) for x in raw_time.split(':')]
        job = updater.job_queue.run_daily(callback=send_quote_of_the_day_to_chat(chat_id),
                                          time=time(hour=hour,
                                                    minute=minute))
        subscriptions[chat_id] = job, raw_time


def save_subscriptions() -> None:
    subs = {}
    for chat_id in subscriptions:
        subs[chat_id] = subscriptions[chat_id][1]
    with open(subscriptions_file, mode='w') as s_file:
        yaml.safe_dump(subs, s_file)


def send_quote_of_the_day(chat_id: int, context: CallbackContext) -> None:
    message_async: Promise = send_text_async(bot=context.bot,
                                             chat_id=chat_id,
                                             text=messages.LOADING)

    quote = restapiservice.get_quote_of_the_day()

    message: Message = message_async.result()
    del message_async
    edit_async(text=messages.QUOTE_OF_THE_DAY(quote),
               bot=context.bot,
               message=message,
               disable_web_page_preview=True)


def send_quote_of_the_day_to_chat(chat_id: int) -> Callable[[CallbackContext], None]:
    def fun(ctxt: CallbackContext) -> None:
        send_quote_of_the_day(chat_id, ctxt)

    return fun


@command_handler
def quotes_handler(update: Update, context: CallbackContext) -> None:
    message_async: Promise = send_text_async(bot=context.bot,
                                             chat_id=update.message.chat_id,
                                             text=messages.LOADING)

    count = restapiservice.get_quotes_count(context.args)
    pages = int((count + PAGE_SIZE - 1) / PAGE_SIZE)

    message: Message = message_async.result()
    edit_async(text=messages.QUOTES_FOUND(count),
               bot=context.bot,
               message=message)

    if count > 0:
        message_async: Promise = send_text_async(bot=context.bot,
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
                   message=message,
                   reply_markup=markup)


@command_handler
def quote_of_the_day_handler(update: Update, context: CallbackContext) -> None:
    send_quote_of_the_day(chat_id=update.message.chat_id,
                          context=context)


@command_handler
def quote_handler(update: Update, context: CallbackContext) -> None:
    pass


@command_handler
def persons_handler(update: Update, context: CallbackContext) -> None:
    message_async: Promise = send_text_async(bot=context.bot,
                                             chat_id=update.message.chat_id,
                                             text=messages.LOADING)

    persons = restapiservice.get_persons(context.args)
    count = len(persons)

    markup = None

    if count > 0:
        keyboard = []
        for person in persons:
            person_id = person['id']
            first_name = person['firstName']
            last_name = person['lastName']
            keyboard.append([InlineKeyboardButton(text=f"{first_name} {last_name}",
                                                  callback_data=f'P{person_id}')])
        markup = InlineKeyboardMarkup(keyboard)

    message: Message = message_async.result()
    edit_async(text=messages.PERSONS_FOUND(count),
               bot=context.bot,
               message=message,
               reply_markup=markup)


@command_handler
def subscribe_handler(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.NO_TIME_ARGUMENT)
        return

    raw_time = context.args[0]
    user_id = update.message.from_user.id

    if user_id in subscriptions and raw_time == subscriptions[user_id][1]:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.ALREADY_SUBSCRIBED(raw_time))
        return

    if not re.match(r'^\d\d:\d\d$', raw_time):
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.INCORRECT_TIME_FORMAT)
        return
    hour, minute = [int(x) for x in raw_time.split(':')]

    if hour > 23:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.INVALID_HOUR)
        return

    if minute > 59:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.INVALID_MINUTE)
        return

    if user_id in subscriptions:
        job, sub_time = subscriptions[user_id]
        job.schedule_removal()

        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.SUBSCRIPTION_REMOVED(sub_time))

    job = context.job_queue.run_daily(callback=send_quote_of_the_day_to_chat(update.message.chat_id),
                                      time=time(hour=hour,
                                                minute=minute))
    subscriptions[user_id] = job, raw_time
    save_subscriptions()

    send_text_async(bot=context.bot,
                    chat_id=update.message.chat_id,
                    text=messages.SUBSCRIPTION_SUCCESSFUL(raw_time))


@command_handler
def unsubscribe_handler(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id not in subscriptions:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.NOT_SUBSCRIBED)
        return

    job, sub_time = subscriptions[user_id]
    job.schedule_removal()
    subscriptions.pop(user_id)
    save_subscriptions()
    send_text_async(bot=context.bot,
                    chat_id=update.message.chat_id,
                    text=messages.SUBSCRIPTION_REMOVED(sub_time))


@command_handler
def random_handler(update: Update, context: CallbackContext) -> None:
    message_async: Promise = send_text_async(bot=context.bot,
                                             chat_id=update.message.chat_id,
                                             text=messages.LOADING)

    quote = restapiservice.get_quote_random(context.args)

    message: Message = message_async.result()
    del message_async
    edit_async(text=messages.QUOTE(quote),
               bot=context.bot,
               message=message,
               disable_web_page_preview=True)


@command_handler
def help_handler(update: Update, context: CallbackContext) -> None:
    send_text_async(bot=context.bot,
                    chat_id=update.message.chat_id,
                    text=messages.HELP)


@query_handler
def quotes_page_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query

    edit_async(text=messages.LOADING,
               bot=context.bot,
               message=query.message,
               reply_markup=None)

    [page, pages] = [int(x) for x in query.data[1:].split(';')]

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
               message=query.message,
               reply_markup=markup)


@query_handler
def person_handler(update: Update, context: CallbackContext) -> None:
    pass


@admin_command_handler
def whitelist_handler(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.NO_USER_ID_ARGUMENT)
        return

    chat_id = int(context.args[0])
    try:
        chat = context.bot.get_chat(chat_id=chat_id)
    except BadRequest:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.USER_NOT_FOUND)
        return

    whitelist(user_chat=chat,
              chat_id=update.message.chat_id,
              context=context)


@admin_command_handler
def blacklist_handler(update: Update, context: CallbackContext) -> None:
    if len(context.args) != 1:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.NO_USER_ID_ARGUMENT)
        return

    chat_id = int(context.args[0])
    try:
        chat = context.bot.get_chat(chat_id=chat_id)
    except BadRequest:
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=messages.USER_NOT_FOUND)
        return

    blacklist(user_chat=chat,
              chat_id=update.message.chat_id,
              context=context)


@admin_command_handler
def stop_handler(update: Update, context: CallbackContext) -> None:
    send_admins_async(text=messages.BOT_STOPPED(update.message.from_user),
                      bot=context.bot)

    def stop():
        updater.is_idle = False
        updater.stop()

    threading.Thread(target=stop).start()


@admin_query_handler
def accept_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query

    remove_markup(bot=context.bot,
                  message=query.message)

    chat_id = int(query.data[1:])
    chat = context.bot.get_chat(chat_id=chat_id)

    if whitelist(user_chat=chat,
                 chat_id=query.message.chat_id,
                 context=context):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.WHITELIST_REQUEST_ACCEPTED)


@admin_query_handler
def deny_handler(update: Update, context: CallbackContext) -> None:
    query: CallbackQuery = update.callback_query

    remove_markup(bot=context.bot,
                  message=query.message)

    chat_id = int(query.data[1:])
    chat = context.bot.get_chat(chat_id=chat_id)

    if blacklist(user_chat=chat,
                 chat_id=query.message.chat_id,
                 context=context):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.WHITELIST_REQUEST_DENIED)


def error_handler(update: Update, context: CallbackContext) -> None:
    code = random.randint(1000, 10000)
    logging.error(f"\nError code: {code}")
    if update.message:
        command = update.message.text
        user = update.message.from_user
        send_admins_async(text=messages.ERROR_COMMAND(command, user, code),
                          bot=context.bot)
        logging.error(f"Command: {command} by user {messages.USERNAME(user)}")
    if update.callback_query:
        query: CallbackQuery = update.callback_query
        data = query.data
        user = query.from_user
        send_admins_async(text=messages.ERROR_QUERY(data, user, code),
                          bot=context.bot)
        logging.error(f"Query: {data} by user {messages.USERNAME(user)}")

    logging.exception(context.error)
    logging.error(f"End of error: {code}")


def unknown_handler(update: Update, context: CallbackContext) -> None:
    send_text_async(bot=context.bot,
                    chat_id=update.message.chat_id,
                    text=messages.UNKNOWN_COMMAND)


if __name__ == '__main__':
    logging.info("Started bot")
    with open(token_file) as t_file:
        token = t_file.readline()
    updater = Updater(token=token, use_context=True)
    del token
    dispatcher = updater.dispatcher
    load_subscriptions()
    dispatcher.add_handler(CommandHandler('quotes', quotes_handler))
    dispatcher.add_handler(CommandHandler('quoteoftheday', quote_of_the_day_handler))
    dispatcher.add_handler(CommandHandler('persons', persons_handler))
    dispatcher.add_handler(CommandHandler('subscribe', subscribe_handler))
    dispatcher.add_handler(CommandHandler('unsubscribe', unsubscribe_handler))
    dispatcher.add_handler(CommandHandler('random', random_handler))
    dispatcher.add_handler(CommandHandler('help', help_handler))
    dispatcher.add_handler(CommandHandler('whitelist', whitelist_handler))
    dispatcher.add_handler(CommandHandler('blacklist', blacklist_handler))
    dispatcher.add_handler(CommandHandler('stop', stop_handler))
    dispatcher.add_handler(CallbackQueryHandler(callback=quotes_page_handler,
                                                pattern=r'^Q'))
    dispatcher.add_handler(CallbackQueryHandler(callback=person_handler,
                                                pattern=r'^P'))
    dispatcher.add_handler(CallbackQueryHandler(callback=accept_handler,
                                                pattern=r'^A'))
    dispatcher.add_handler(CallbackQueryHandler(callback=deny_handler,
                                                pattern=r'^D'))
    dispatcher.add_error_handler(error_handler)
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_handler))
    dispatcher.add_handler(MessageHandler(Filters.text, top_secret_text_handler))
    dispatcher.add_handler(MessageHandler(Filters.sticker, top_secret_sticker_handler))
    try:
        updater.start_polling()
        logging.info("Successfully started polling.")
        updater.idle()
        logging.info("Stopped bot gracefully.")
    except Unauthorized as err:
        logging.error("Your token seems to be incorrect, bot was not able to start polling.")
