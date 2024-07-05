import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

