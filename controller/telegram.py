
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import asyncio

import re
from telegram import Bot
from config.config import TELEGRAM_API_TOKEN, CHAT_ID
from controller.logger.logger_setup import logger


def remove_icons(text):
    return re.sub(r'[^\w\s:.,$]', '', text)

def send(message):
    bot =Bot(token=TELEGRAM_API_TOKEN)
    asyncio.run(bot.send_message(chat_id=CHAT_ID, text=message))
    logger.info(remove_icons(message))