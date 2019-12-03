import logging
from typing import Union, Callable, List

from telegram import Bot, InlineKeyboardMarkup, Update, Message, User, InlineKeyboardButton, ReplyMarkup
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

import messages

administrators_file = 'administrators.yml'
blacklist_file = 'blacklist.yml'
whitelist_file = 'whitelist.yml'
requests_file = 'requests.yml'


def read(filename: str) -> List[int]:
    with open(filename) as file:
        return [int(line) for line in file.readlines()]


def append(filename: str, user_id: int) -> None:
    with open(filename) as file:
        user_ids = file.readlines()
    user_ids.append(str(user_id) + '\n')
    with open(filename, 'w') as file:
        file.writelines(user_ids)


def remove(filename: str, user_id: int) -> None:
    with open(filename, 'r') as file:
        user_ids = file.readlines()
    user_ids.remove(str(user_id) + '\n')
    with open(filename, 'w') as file:
        file.writelines(user_ids)


def whitelist(user_id: int, chat_id: int, context: CallbackContext) -> bool:
    if user_id in read(whitelist_file) or user_id in read(administrators_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.ALREADY_WHITELISTED)
        return False

    if user_id in read(blacklist_file):
        remove(filename=blacklist_file,
               user_id=user_id)

    append(filename=whitelist_file,
           user_id=user_id)

    send_async(bot=context.bot,
               chat_id=chat_id,
               text=messages.USER_WHITELISTED)

    return True


def blacklist(user_id: int, chat_id: int, context: CallbackContext) -> bool:
    if user_id in read(administrators_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.CANNOT_BLACKLIST_ADMINISTRATOR)
        return False

    if user_id in read(blacklist_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.ALREADY_BLACKLISTED)
        return False

    if user_id in read(whitelist_file):
        remove(filename=whitelist_file,
               user_id=user_id)

    append(filename=blacklist_file,
           user_id=user_id)

    send_async(bot=context.bot,
               chat_id=chat_id,
               text=messages.USER_BLACKLISTED)

    return True


def is_authorized(user: User, chat_id: int, context: CallbackContext) -> bool:
    user_id = user.id
    if user_id in read(administrators_file) or user_id in read(whitelist_file):
        return True
    if user_id in read(requests_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.PENDING)
    elif user_id in read(blacklist_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.BLACKLISTED)
    else:
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.NOT_WHITELISTED)
        append(filename=requests_file,
               user_id=user_id)
        username = user.username
        keyboard = [[InlineKeyboardButton("Deny", callback_data=f"D{user_id};{chat_id}"),
                     InlineKeyboardButton("Accept", callback_data=f"A{user_id};{chat_id}")]]
        markup = InlineKeyboardMarkup(keyboard)
        send_admins_async(text=messages.WHITELIST_REQUEST(username=username,
                                                          user_id=user_id),
                          context=context,
                          reply_markup=markup)
    return False


def is_whitelisted(user_id: int):
    return user_id in read(whitelist_file)


def is_blacklisted(user_id: int):
    return user_id in read(blacklist_file)


def command_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext):
        if update.edited_message:
            return
        try:
            logging.info(f"Command {update.message.text} by {update.message.from_user.username}")
            if is_authorized(update.message.from_user, update.message.chat_id, context):
                handler(update, context)
        except Exception as err:
            if update.message.from_user.id not in read(administrators_file):
                send_async(bot=context.bot,
                           chat_id=update.callback_query.message.chat_id,
                           text=messages.ERROR_OCCURRED)
            raise err

    return func


def query_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext):
        try:
            logging.info(f"Query {update.callback_query.data} by {update.callback_query.from_user.username}")
            if is_authorized(update.callback_query.from_user, update.callback_query.message.chat_id, context):
                handler(update, context)
        except Exception as err:
            if update.callback_query.from_user.id not in read(administrators_file):
                send_async(bot=context.bot,
                           chat_id=update.callback_query.message.chat_id,
                           text=messages.ERROR_OCCURRED)
            raise err

    return func


def admin_command_handler(handler: Callable[[Update, CallbackContext], None]) \
        -> Callable[[Update, CallbackContext], None]:
    @command_handler
    def func(update: Update, context: CallbackContext):
        if update.message.chat_id in read(administrators_file):
            handler(update, context)
        else:
            send_async(bot=context.bot,
                       chat_id=update.message.chat_id,
                       text=messages.NO_PERMISSION)
            username = update.message.from_user.username
            command = update.message.text
            send_admins_async(text=messages.NO_PERMISSION_REPORT(username=username,
                                                                 command=command),
                              context=context)

    return func


def admin_query_handler(handler: Callable[[Update, CallbackContext], None]) \
        -> Callable[[Update, CallbackContext], None]:
    @query_handler
    def func(update: Update, context: CallbackContext):
        if update.callback_query.message.chat_id in read(administrators_file):
            handler(update, context)
        else:
            send_async(bot=context.bot,
                       chat_id=update.message.chat_id,
                       text=messages.NO_PERMISSION)
            username = update.message.from_user.username
            command = update.message.text
            send_admins_async(text=messages.NO_PERMISSION_REPORT(username=username,
                                                                 command=command),
                              context=context)

    return func


def send_admins_async(text: str,
                      context: CallbackContext,
                      reply_markup: InlineKeyboardMarkup = None):
    for chat_id in read(administrators_file):
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=text,
                   reply_markup=reply_markup)


@run_async
def send_async(bot: Bot,
               chat_id: Union[int, str],
               text: str,
               disable_web_page_preview: bool = True,
               reply_to_message_id: int = None,
               reply_markup: ReplyMarkup = None):
    return bot.sendMessage(chat_id=chat_id,
                           text=text,
                           display_web_page_preview=disable_web_page_preview,
                           reply_to_message_id=reply_to_message_id,
                           reply_markup=reply_markup)


@run_async
def edit_async(text: str,
               bot: Bot,
               message: Message,
               disable_web_page_preview: bool = None,
               reply_markup: ReplyMarkup = None):
    return bot.editMessageText(text=text,
                               chat_id=message.chat_id,
                               message_id=message.message_id,
                               display_web_page_preview=disable_web_page_preview,
                               reply_markup=reply_markup)


@run_async
def remove_markup(bot: Bot,
                  message: Message):
    bot.editMessageReplyMarkup(chat_id=message.chat_id,
                               message_id=message.message_id)
