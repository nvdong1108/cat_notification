
import re
import asyncio
import socket

from common.format_until import format_price, format_amt
from version import __version__
from config.config import TELEGRAM_API_TOKEN, CHAT_ID
from telegram import Bot
from logger.logger_setup import logger

from common.constants import *


def remove_icons(text):
    return re.sub(r'[^\w\s:.,$]', '', text)


async def send(message):
    bot = Bot(token=TELEGRAM_API_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)
    logger.info(remove_icons(message))


async def notification_device_name():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        message = (
            f"\n"
            f"🏃‍♂️🏃‍♂️🏃‍♂️💨\n"
            f"Version: {__version__}\n"
            f"Hostname: {hostname}\n"
            f"IP Address: {ip_address}\n"
        )
        await send(message)
    except Exception as e:
        print(f"get info ip error {e}")


async def notification_take_profit_order(price, profit):
    message = (
        "🎉🎉🎉\n\n"
        f"TAKE PROFIT Price : {format_price(price)}\n"
        f"Profit : {format_amt(profit)}\n"
        f"\n"
    )
    await send(message)

async def notification_stop_loss_order(price, lost):
    message = (
        "💣💣\n\n"
        f"STOP LOSS Price : {format_price(price)}\n"
        f"Lost : {format_amt(lost)}\n"
        f"\n"
    )
    await send(message)


def get_content_title(title):
    if title =='RSI1' or title == INTERVAL_1M:
        return "🚨 RSI 1m"
    elif title =='RSI15' or title == INTERVAL_15M:
        return "🚨🚨🚨 RSI 15m"
    return '🚨🚨🚨🚨🚨'


# def notif_new_buy_order(formatted_rsi, btc_price):
#     message = (
#         ""
#         f"{get_content_title(INTERVAL_1M)}\n\n"
#         f"Value is {formatted_rsi} advice to buy 📈 \n"
#         f" Buying price is {format_price(btc_price)}\n"
#         f"Take Stoploss  {format_price(stop_loss_price)}\n"
#         f"Take Profit  {format_price(take_profit_price)}\n"
#         f"\n"
#         f"💲 margin : {format_amt(cost_per_trade)} 💪 x{LEVERAGE}\n"
#         f"💣 max stoploss : {format_price(calcu_stop_loss(side, btc_price))}\n"
#         f"Rate SL/TP is {TP_RATE}/{TP_RATE}\n"
#         f"CreateTime  {formatted_time}\n"
#     )
# send(message)