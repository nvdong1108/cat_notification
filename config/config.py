import os
from dotenv import load_dotenv

load_dotenv()

CHAT_ID = os.getenv('CHAT_ID')
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
"""
BINANCE_API_KEY = os.getenv('BINANCE_TETNET_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_TETNET_API_SECRET')
"""

