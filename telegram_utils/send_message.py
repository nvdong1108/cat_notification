import asyncio
from telegram import Bot

async def send (message):
    api_token = "6837177530:AAFUTQeVB7zf7pR6z_8iJFZYxxY7WYdLSN4"
    chat_id = "-4251336843"
    bot = Bot(token=api_token)
    await bot.send_message(chat_id=chat_id, text=message)


