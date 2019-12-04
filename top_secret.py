from typing import Dict

import yaml
from telegram import Update
from telegram.ext import CallbackContext

from utils import send_async

secrets_file = 'secrets.yml'


def read(filename: str) -> Dict[str, str]:
    try:
        with open(filename) as file:
            return yaml.safe_load(file) or {}
    except FileNotFoundError:
        return {}


def top_secret_handler(update: Update, context: CallbackContext) -> None:
    text: str = update.message.text
    secrets = read(secrets_file)
    if text.lower() in secrets:
        send_async(bot=context.bot,
                   chat_id=update.message.chat_id,
                   text=secrets[text.lower()])
