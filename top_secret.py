import logging
from typing import Dict

import yaml
from telegram import Update
from telegram.ext import CallbackContext

import messages
from utils import send_text_async, send_sticker_async

secrets_file = 'secrets.yml'


def read(filename: str) -> Dict[str, Dict[str, str]]:
    try:
        with open(filename, encoding='UTF-8') as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}


def top_secret_text_handler(update: Update, context: CallbackContext) -> None:
    text: str = update.message.text
    if text[-1] in "?!.":
        text = text[:-1]
    secrets = read(secrets_file)['texts']
    if text.lower() in secrets:
        logging.info(f"{messages.USERNAME(update.message.from_user)} discovered secret {text}!")
        send_text_async(bot=context.bot,
                        chat_id=update.message.chat_id,
                        text=secrets[text.lower()])
    else:
        logging.info(f"{messages.USERNAME(update.message.from_user)} sent {text}!")


def top_secret_sticker_handler(update: Update, context: CallbackContext) -> None:
    sticker: str = update.message.sticker.file_id
    secrets = read(secrets_file)['stickers']
    if sticker in secrets:
        logging.info(f"{messages.USERNAME(update.message.from_user)} discovered secret sticker {sticker}!")
        send_sticker_async(bot=context.bot,
                           chat_id=update.message.chat_id,
                           sticker=secrets[sticker])
    else:
        logging.info(f"{messages.USERNAME(update.message.from_user)} sent {sticker}!")
