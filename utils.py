import logging
from typing import Union, Callable, List

from telegram import Bot, InlineKeyboardMarkup, Update, Message, User, InlineKeyboardButton, ReplyKeyboardMarkup, \
    ReplyMarkup
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

import messages


administrators_file = 'administrators.yml'
blacklist_file = 'blacklist.yml'
whitelist_file = 'whitelist.yml'


def read_administrators() -> List[int]:
    with open(administrators_file) as a_file:
        return [int(line) for line in a_file.readlines()]


def read_blacklist() -> List[int]:
    with open(blacklist_file) as b_file:
        return [int(line) for line in b_file.readlines()]


def append_blacklist(user_id: int) -> None:
    with open(blacklist_file, 'a') as b_file:
        b_file.write(str(user_id))


def remove_blacklist(user_id: int) -> None:
    with open(blacklist_file, 'r') as b_file:
        user_ids = b_file.readlines()
    user_ids.remove(str(user_id))
    with open(blacklist_file, 'w') as b_file:
        b_file.writelines(user_ids)


def read_whitelist() -> List[int]:
    with open(whitelist_file) as w_file:
        return [int(line) for line in w_file.readlines()]


def append_whitelist(user_id: int) -> None:
    with open(whitelist_file, 'a') as w_file:
        w_file.write(str(user_id))


def remove_whitelist(user_id: int) -> None:
    with open(whitelist_file) as w_file:
        user_ids = w_file.readlines()
    user_ids.remove(str(user_id))
    with open(whitelist_file, 'w') as w_file:
        w_file.writelines(user_ids)


def whitelist(user_id: int, chat_id: int, context: CallbackContext):
    if user_id in read_whitelist() or user_id in read_administrators():
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.ALREADY_WHITELISTED)
        return

    if user_id in read_blacklist():
        remove_blacklist(user_id=user_id)

    append_whitelist(user_id=user_id)

    send_async(bot=context.bot,
               chat_id=chat_id,
               text=messages.USER_WHITELISTED)


def blacklist(user_id: int, chat_id: int, context: CallbackContext):
    if user_id in read_administrators():
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.CANNOT_BLACKLIST_ADMINISTRATOR)
        return

    if user_id in read_blacklist():
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.ALREADY_BLACKLISTED)
        return

    if user_id in read_whitelist():
        remove_whitelist(user_id=user_id)

    append_blacklist(user_id=user_id)

    send_async(bot=context.bot,
               chat_id=chat_id,
               text=messages.USER_BLACKLISTED)


def is_authorized(user: User, chat_id: int, context: CallbackContext) -> bool:
    user_id = user.id
    if user_id in read_administrators() or user_id in read_whitelist():
        return True
    if user_id in read_blacklist():
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.BLACKLISTED)
    else:
        send_async(bot=context.bot,
                   chat_id=chat_id,
                   text=messages.NOT_WHITELISTED)
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
    return user_id in read_whitelist()


def is_blacklisted(user_id: int):
    return user_id in read_blacklist()


def command_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext):
        if update.edited_message:
            return
        try:
            logging.info(f"Command {update.message.text} by {update.message.from_user.username}")
            if is_authorized(update.message.from_user, update.message.chat_id, context):
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
            if is_authorized(update.callback_query.from_user, update.callback_query.message.chat_id, context):
                handler(update, context)
        except Exception as err:
            send_async(bot=context.bot,
                       chat_id=update.callback_query.message.chat_id,
                       text=messages.ERROR_OCCURRED)
            raise err

    return func


def admin_command_handler(handler: Callable[[Update, CallbackContext], None]) \
        -> Callable[[Update, CallbackContext], None]:
    @command_handler
    def func(update: Update, context: CallbackContext):
        if update.message.chat_id in read_administrators():
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
        if update.callback_query.message.chat_id in read_administrators():
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
    for chat_id in read_administrators():
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
