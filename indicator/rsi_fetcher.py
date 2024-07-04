import socket
import re
import ccxt
import pandas as pd
import ta
import time
import asyncio
from telegram import Bot
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from logger.logger_setup import logger

API_TOKEN = "6837177530:AAFUTQeVB7zf7pR6z_8iJFZYxxY7WYdLSN4"
CHAT_ID = "-4266638402"
quantity_per_trade = 0.002
sl_rate = 0.5
tp_rate = 0.5
leverage = 50

isOpenOrder = False
stop_loss_price = 0
take_profit_price = 0
btc_usdt_price = 0

def format_amt(amt): 
    return f"{amt:.2f} USDT"

def format_price(amt):
    return f"{int(amt):,} USDT"

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def fetch_ohlcv_with_retry(symbol, timeframe, limit):
    binance = ccxt.binance()
    return binance.fetch_ohlcv(symbol, timeframe, limit=limit)

def fetch_ohlcv(symbol, timeframe, limit=100):
    ohlcv = fetch_ohlcv_with_retry(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df


def calculate_rsi(df, period=14):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=period).rsi()
    return df

def remove_icons(text):
    return re.sub(r'[^\w\s:.,$]', '', text)

async def send(message):
    bot = Bot(token=API_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=message)
    logger.info(remove_icons(message))

@retry(stop=stop_after_attempt(3), wait=wait_fixed(5))
def get_current_btc_usdt_price():
    binance = ccxt.binance()
    try:
        ticker = binance.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        return current_price
    except Exception as e:
        logger.info(f"Error fetching BTC/USDT price: {e}")
        return None

def calcu_stop_loss(cost_per_trade,side , entry):
    if 'SELL' == side:
        return entry * (1+1/leverage)
    else:
        return entry * (1-1/leverage)
    
def calcu_tk_stop_loss(cost_per_trade,side , entry):
    if 'SELL' == side:
        return (entry + ((cost_per_trade / quantity_per_trade) * sl_rate))
    else:
        return entry - ((cost_per_trade / quantity_per_trade) * sl_rate)
       
def calcu_take_profit(cost_per_trade,side , entry):
    if 'SELL' == side:
        return entry - ((cost_per_trade / quantity_per_trade) * tp_rate)
    else:
        return entry + ((cost_per_trade / quantity_per_trade) * tp_rate)

 
async def new_order(rsi,side,btc_price):
    logger.info(f"=========== NEW ORDER {side} ===========")
    #btc_usdt_price_new = None
    index = 0
    global take_profit_price , stop_loss_price
    
    formatted_rsi = f"{rsi:.2f}"
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y/%m/%d %H:%M:%S")
    cost_per_trade =  quantity_per_trade * btc_price  / leverage
    stop_loss_price = calcu_tk_stop_loss(cost_per_trade,side,btc_price)
    take_profit_price = calcu_take_profit(cost_per_trade,side,btc_price)

    message = (
        "🚨🚨🚨\n\n"
        f"Timestamp : {formatted_time}\n"
        f"RSI : {formatted_rsi}\n"
        f"Action : {side}\n"
        f"Entry Price : {format_price(btc_price)}\n"
        f"Take Stoploss : {format_price(stop_loss_price)}\n"
        f"Take Profit : {format_price(take_profit_price)}\n"
        f"\n\n"
        f"💲 : {format_amt(cost_per_trade)} 💪 x{leverage}\n"
        f"💣 : {format_price(calcu_stop_loss(cost_per_trade,side,btc_price))}\n"
    )
    await send(message)

async def noti_done_order(type,price):
    if type == "TP" :
        message = (
            "🎉🎉🎉\n\n"
            f"TAKE PROFIT Price : {format_price(price)}\n"
            f"\n"  
        )               
    else:
        message = (
            "💣💣\n\n"
            f"STOP LOSS Price : {format_price(price)}\n"  
            f"\n"
        )  
    await send(message)


async def validateOrder(price):
    if not isOpenOrder:
        return False
    if price >= take_profit_price : 
        logger.info("CLOSE => TAKE PROFIT ")
        await noti_done_order("TP",price)
        return True
    if price <= stop_loss_price :
        logger.info("CLOSE => STOP LOSS")
        await noti_done_order("SL",price)
        return True
    return False

async def main(symbol='BTC/USDT', period=14, interval=60):
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        message=(
                f"\n"
                f"🏃‍♂️🏃‍♂️🏃‍♂️💨\n" 
                 f"Hostname : {hostname}\n"
                 f"IP Address : {ip_address}\n"
                )
        await send(message)
    except Exception as e:
        print(f"get info ip error {e}")    
    global isOpenOrder, take_profit_price, stop_loss_price
    while True:
        time.sleep(interval)
        price_btc =  get_current_btc_usdt_price()
        # co 1 lenh dang mo 
        if isOpenOrder : 
            
            # kiểm tra lênh đang mở chạm TP hay SL
            is_act_close=await validateOrder(price_btc)  
            if not is_act_close:
                logger.info(f"Alert ! BTC price is {format_price(price_btc)}")
                continue
            # reset dữ liệu lệnh cũ, tiếp tục tìm lệnh mới . 
            isOpenOrder = False
            take_profit_price = 0
            stop_loss_price= 0
            #     
        df_15m = fetch_ohlcv(symbol, '15m')
        df_15m = calculate_rsi(df_15m, period)
        current_rsi_15m = df_15m['rsi'].iloc[-1]
        k = 25
        if current_rsi_15m < (50-k):
            if not isOpenOrder:
                await new_order(current_rsi_15m,"BUY",price_btc)
                isOpenOrder = True
        elif current_rsi_15m > (50+k):
            if not isOpenOrder:
                await new_order(current_rsi_15m,"SELL",price_btc)
                isOpenOrder = True
        message = f"RSI Alert! Current RSI for {symbol} on 15m is {current_rsi_15m:.2f} price {format_price(price_btc)}"
        logger.info(message)

if __name__ == "__main__":
    print("start ...")
    logger.info("\n\n\t===============> BEGIN RUN <===============\n")
    
    asyncio.run(main())
