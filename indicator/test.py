
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


import pandas as pd
import pandas_ta as ta
import websocket
import json
import time
import requests

from collections import deque


# Khai báo một hàng đợi để lưu trữ giá
price_window = deque(maxlen=300)  # Lưu 5 phút dữ liệu (khoảng 5 * 60 giây)


ohlc_data = []

def get_ohlc_data(symbol='BTCUSDT', interval='1m', limit=10):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    ohlc = []
    for candle in data:
        ohlc.append({
            'open': float(candle[1]),
            'high': float(candle[2]),
            'low': float(candle[3]),
            'close': float(candle[4])
        })
    return ohlc


def on_message(ws, message):
    global price_window
    data = json.loads(message)
    current_price = float(data['p'])

    price_window.append(current_price)

    if ohlc_data:
        last_open = ohlc_data[-1]['close']
        last_high = max(last_open, current_price)
        last_low = min(last_open, current_price)
    else:
        last_open = current_price
        last_high = current_price
        last_low = current_price

    ohlc_data.append({
        'open': last_open,  # Giá mở
        'high': last_high,  # Giá cao nhất
        'low': last_low,   # Giá thấp nhất
        'close': current_price   # Giá đóng
    })

    if len(ohlc_data) >= 10:  # Để tính toán với 10 cây nến
        df = pd.DataFrame(ohlc_data[-10:])  # Lấy 10 cây nến gần nhất

        # Tính toán các mô hình nến
        df['CDLENGULFING'] = ta.cdl_engulfing(df['open'], df['high'], df['low'], df['close'])

        # Kiểm tra và in ra mô hình nến hiện tại
        if df['CDLENGULFING'].iloc[-1] != 0:
            print("Mô hình nến: Bullish/Bearish Engulfing")

def on_error(ws, error):
    print(f"Lỗi: {error}")

def on_close(ws):
    print("WebSocket đóng.")

def on_open(ws):
    print("WebSocket kết nối thành công.")

# Kết nối tới WebSocket của Binance
def run_websocket():
    ws_url = "wss://stream.binance.com:9443/ws/btcusdt@trade"  # Lấy giá BTC/USDT
    ws = websocket.WebSocketApp(ws_url,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

# Chạy WebSocket trong một luồng riêng để tránh chặn
if __name__ == "__main__":
    while True:
        run_websocket()
        time.sleep(60)  # Chờ 1 phút trước khi kiểm tra lại