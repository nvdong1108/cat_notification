
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import pandas as pd
import ta
from binance.client import Client
from  config.config import BINANCE_API_KEY,BINANCE_API_SECRET


client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def get_btcusdt_1m_klines():
    klines = client.get_klines(symbol='BTCUSDT', interval=Client.KLINE_INTERVAL_1MINUTE)
    data = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    data['close'] = data['close'].astype(float)
    return data

def is_rsi_turnaround(rsi_series):

    overbought_threshold = 70
    oversold_threshold = 30

    overbought_index = (rsi_series > overbought_threshold).idxmax()
    if rsi_series[overbought_index] <= overbought_threshold:
        return False, -1

    highest_rsi = rsi_series[overbought_index:].max()
    highest_rsi_index = rsi_series[overbought_index:].idxmax()

    if highest_rsi_index > overbought_index and (rsi_series[highest_rsi_index] - rsi_series[highest_rsi_index - 1]) >= 2:
        return True, highest_rsi_index

    return False, -1

def main():
    df = get_btcusdt_1m_klines()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()

    turnaround, index = is_rsi_turnaround(df['rsi'])
    print("Điểm quay đầu:", turnaround)
    print("Vị trí quay đầu:", index)

if __name__ == "__main__":
    main()
