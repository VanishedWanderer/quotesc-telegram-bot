import logging

from telegram.ext import Updater

from utils import read_token

updater = Updater(token=read_token(), use_context=True)
dispatcher = updater.dispatcher
