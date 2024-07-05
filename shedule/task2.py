import sys
import os
import json
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import time
import websocket
from datetime import datetime, timedelta
from binance.client import Client
from telegram import Bot
from config.config import TELEGRAM_API_TOKEN,CHAT_ID, BINANCE_API_SECRET,BINANCE_API_KEY

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
bot = Bot(token=TELEGRAM_API_TOKEN)


highest_price = 0
lowest_price = float('inf')
last_checked_time = datetime.now()

def format_price(amt):
    return f"{int(amt):,}"

def send_telegram_message(message):
    bot.send_message(chat_id=CHAT_ID, text=message)

def on_message(ws, message):
    global highest_price,lowest_price, last_checked_time

    msg = json.loads(message)
    current_time = datetime.now()
    current_price =int(float(msg['p']))
    
    if current_price > highest_price or current_time - last_checked_time > timedelta(minutes=15):
        highest_price = current_price
        lowest_price = current_price  
        last_checked_time = current_time
    elif current_price < lowest_price:
        lowest_price = current_price

    
    if highest_price > 0 and (highest_price - current_price) / highest_price * 100 >= 2:
        message = f'Giá BTC đã giảm {((highest_price - current_price) / highest_price * 100):.2f}% từ giá cao nhất trong 15 phút qua. Giá hiện tại: {current_price:.2f} USDT'
        send_telegram_message(message)
        highest_price = current_price 

    if lowest_price < float('inf') and (current_price - lowest_price) / lowest_price * 100 >= 2:
        message = f'Giá BTC đã giảm {((current_price - lowest_price) / lowest_price * 100):.2f}% từ giá thấp nhất trong 15 phút qua. Giá hiện tại: {current_price:.2f} USDT'
        send_telegram_message(message)
        lowest_price = current_price  

    print(f"Price BTC {format_price(current_price)} , Highest {format_price(highest_price)} , lowest {format_price(lowest_price)}")

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    print("### opened ###")

def main():
    ws = websocket.WebSocketApp("wss://stream.binance.com:9443/ws/btcusdt@trade",
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == '__main__':
    main()