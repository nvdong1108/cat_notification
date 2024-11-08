

import pandas_ta as ta
import pandas as pd

from common.format_until import format_rsi, format_price
from binance.client import Client

from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


def fetch_rsi(interval):

    klines = client.futures_klines(symbol='BTCUSDT', interval=interval, limit='500')
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'number_of_trades',
                                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)

    df['rsi'] = ta.rsi(df['close'], length=14)

    current_price = format_price(df['close'].iloc[-1])
    current_rsi = format_rsi(df['rsi'].iloc[-1])
    recent_rsi = df['rsi'].iloc[-20:]
    max_rsi = format_rsi(recent_rsi.max())
    min_rsi = format_rsi(recent_rsi.min())

    return current_price, current_rsi, max_rsi, min_rsi


def fetch_indicators(interval):
    klines = client.futures_klines(symbol='BTCUSDT', interval=interval, limit=500)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'number_of_trades',
                                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])

    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)

    # Tính RSI
    df['rsi'] = ta.rsi(df['close'], length=14)

    # Tính ADX
    df['adx'] = ta.adx(df['high'], df['low'], df['close'], length=14)['ADX_14']

    # Lấy giá trị RSI và ADX gần nhất
    latest_rsi = format_rsi(df['rsi'].iloc[-1])
    latest_adx = format_rsi(df['adx'].iloc[-1])
    current_price = df['close'].iloc[-1]

    return latest_rsi, latest_adx, current_price
