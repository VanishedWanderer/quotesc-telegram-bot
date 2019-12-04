import logging
from typing import Union, Callable, Dict

import yaml
from telegram import Bot, InlineKeyboardMarkup, Update, Message, User, InlineKeyboardButton, ReplyMarkup, Chat, Sticker
from telegram.ext import CallbackContext
from telegram.ext.dispatcher import run_async

import messages

administrators_file = 'administrators.yml'
blacklist_file = 'blacklist.yml'
whitelist_file = 'whitelist.yml'
requests_file = 'requests.yml'


def read(filename: str) -> Dict[int, str]:
    try:
        with open(filename, encoding='UTF-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}


def append(filename: str, user_chat: Union[User, Chat]) -> None:
    with open(filename, encoding='UTF-8') as file:
        users: Dict = yaml.safe_load(file) or {}
    users.update({user_chat.id: messages.USERNAME(user_chat)})
    with open(filename, mode='w', encoding='UTF-8') as file:
        yaml.safe_dump(users, file)


def remove(filename: str, user_chat: Union[User, Chat]) -> None:
    with open(filename, encoding='UTF-8') as file:
        users: Dict = yaml.safe_load(file) or {}
    if user_chat.id in users:
        users.pop(user_chat.id)
        with open(filename, mode='w', encoding='UTF-8') as file:
            yaml.safe_dump(users, file)


def whitelist(user_chat: Union[User, Chat], chat_id: int, context: CallbackContext) -> bool:
    if user_chat.id in read(whitelist_file) or user_chat.id in read(administrators_file):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.ALREADY_WHITELISTED(user_chat))
        return False

    if user_chat.id in read(blacklist_file):
        remove(filename=blacklist_file,
               user_chat=user_chat)

    append(filename=whitelist_file,
           user_chat=user_chat)

    remove(filename=requests_file,
           user_chat=user_chat)

    send_text_async(bot=context.bot,
                    chat_id=chat_id,
                    text=messages.USER_WHITELISTED(user_chat))

    return True


def blacklist(user_chat: Union[User, Chat], chat_id: int, context: CallbackContext) -> bool:
    if user_chat.id in read(administrators_file):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.CANNOT_BLACKLIST_ADMINISTRATOR)
        return False

    if user_chat.id in read(blacklist_file):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.ALREADY_BLACKLISTED(user_chat))
        return False

    if user_chat.id in read(whitelist_file):
        remove(filename=whitelist_file,
               user_chat=user_chat)

    append(filename=blacklist_file,
           user_chat=user_chat)

    remove(filename=requests_file,
           user_chat=user_chat)

    send_text_async(bot=context.bot,
                    chat_id=chat_id,
                    text=messages.USER_BLACKLISTED(user_chat))

    return True


def is_authorized(user_chat: Union[User, Chat], chat_id: int, context: CallbackContext) -> bool:
    if user_chat.id in read(administrators_file) or user_chat.id in read(whitelist_file):
        return True
    if user_chat.id in read(requests_file):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.PENDING)
    elif user_chat.id in read(blacklist_file):
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.BLACKLISTED)
    else:
        send_text_async(bot=context.bot,
                        chat_id=chat_id,
                        text=messages.NOT_WHITELISTED)
        append(filename=requests_file,
               user_chat=user_chat)
        keyboard = [[InlineKeyboardButton("Deny", callback_data=f"D{chat_id}"),
                     InlineKeyboardButton("Accept", callback_data=f"A{chat_id}")]]
        markup = InlineKeyboardMarkup(keyboard)
        send_admins_async(text=messages.WHITELIST_REQUEST(user_chat=user_chat),
                          context=context,
                          reply_markup=markup)
    return False


def is_whitelisted(user_id: int) -> bool:
    return user_id in read(whitelist_file)


def is_blacklisted(user_id: int) -> bool:
    return user_id in read(blacklist_file)


def command_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext) -> None:
        if update.edited_message:
            return
        try:
            logging.info(f"Command {update.message.text} by {messages.USERNAME(update.message.from_user)}")
            if is_authorized(update.message.from_user, update.message.chat_id, context):
                handler(update, context)
        except Exception as err:
            if update.message.from_user.id not in read(administrators_file):
                send_text_async(bot=context.bot,
                                chat_id=update.callback_query.message.chat_id,
                                text=messages.ERROR_OCCURRED)
            raise err

    return func


def query_handler(handler: Callable[[Update, CallbackContext], None]) -> Callable[[Update, CallbackContext], None]:
    def func(update: Update, context: CallbackContext) -> None:
        try:
            logging.info(f"Query {update.callback_query.data} by {messages.USERNAME(update.callback_query.from_user)}")
            if is_authorized(update.callback_query.from_user, update.callback_query.message.chat_id, context):
                handler(update, context)
        except Exception as err:
            if update.callback_query.from_user.id not in read(administrators_file):
                send_text_async(bot=context.bot,
                                chat_id=update.callback_query.message.chat_id,
                                text=messages.ERROR_OCCURRED)
            raise err

    return func


def admin_command_handler(handler: Callable[[Update, CallbackContext], None]) \
        -> Callable[[Update, CallbackContext], None]:
    @command_handler
    def func(update: Update, context: CallbackContext) -> None:
        if update.message.chat_id in read(administrators_file):
            handler(update, context)
        else:
            send_text_async(bot=context.bot,
                            chat_id=update.message.chat_id,
                            text=messages.NO_PERMISSION)
            user = update.message.from_user
            command = update.message.text
            send_admins_async(text=messages.NO_PERMISSION_REPORT(user_chat=user,
                                                                 command=command),
                              context=context)

    return func


def admin_query_handler(handler: Callable[[Update, CallbackContext], None]) \
        -> Callable[[Update, CallbackContext], None]:
    @query_handler
    def func(update: Update, context: CallbackContext) -> None:
        if update.callback_query.message.chat_id in read(administrators_file):
            handler(update, context)
        else:
            send_text_async(bot=context.bot,
                            chat_id=update.message.chat_id,
                            text=messages.NO_PERMISSION)
            user = update.callback_query.from_user
            command = update.message.text
            send_admins_async(text=messages.NO_PERMISSION_REPORT(user_chat=user,
                                                                 command=command),
                              context=context)

    return func


@run_async
def send_admins_async(text: str,
                      bot: Bot,
                      reply_markup: InlineKeyboardMarkup = None):
    for chat_id in read(administrators_file):
        send_text_async(bot=bot,
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup)


@run_async
def send_text_async(bot: Bot,
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
def send_sticker_async(bot: Bot,
                       chat_id: Union[int, str],
                       sticker: Union[str, Sticker]):
    return bot.sendSticker(chat_id=chat_id,
                           sticker=sticker)


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
                  message: Message) -> None:
    bot.editMessageReplyMarkup(chat_id=message.chat_id,
                               message_id=message.message_id)
