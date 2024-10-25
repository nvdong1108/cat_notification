

import pandas_ta as ta
import pandas as pd

from common.format_until import format_rsi
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

    return format_rsi(df['rsi'].iloc[-1])
