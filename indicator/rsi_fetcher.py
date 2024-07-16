
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import socket
import re
import ccxt
import pandas as pd
import ta
import asyncio
from telegram import Bot
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from config.config import TELEGRAM_API_TOKEN, CHAT_ID
from logger.logger_setup import logger
from version import __version__
from config.mongoDB import insert_order, update_order, select_orders_by_status


quantity_per_trade = 0.002
sl_rate = 0.4
tp_rate = 0.4
leverage = 50

isOpenOrder = False
is_side_open = ""
stop_loss_price = 0
take_profit_price = 0
btc_usdt_price = 0
cost_per_trade = 0

interval_15m = '15m'
interval_1m = '1m'
interval_main = '15m'


def format_amt(amt): 
    if amt is None:
        raise ValueError(f"E003. Value amt is None")
    try:
        return f"{amt:.2f} USDT"
    except (Exception):
        raise Exception(f"Can't format_amt value amt. Amt is {amt} ")
    

def format_price(amt):
    if amt is None:
        raise ValueError(f"E001. Value amt is None")
    try:
        amt_int =int(amt)
    except (ValueError, TypeError):
         raise ValueError(f"E002. Value amt is format wrong. Amt is {amt}, can't convert to int")
    return f"{amt_int:,} USDT"


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
    bot = Bot(token=TELEGRAM_API_TOKEN)
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


def get_content_title(title):
    if title =='RSI1':
        return "🚨 RSI 1m"
    elif title =='RSI15':
            return "🚨🚨🚨 RSI 15m"
    return '🚨🚨🚨🚨🚨'


async def new_order(rsi,side,btc_price,title):
    logger.info(f"=========== NEW ORDER {side} ===========")
    #btc_usdt_price_new = None
    index = 0
    global take_profit_price , stop_loss_price, sl_rat, tp_rate, cost_per_trade
    
    formatted_rsi = f"{rsi:.2f}"
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y/%m/%d %H:%M:%S")
    cost_per_trade =  quantity_per_trade * btc_price  / leverage
    stop_loss_price = calcu_tk_stop_loss(cost_per_trade,side,btc_price)
    take_profit_price = calcu_take_profit(cost_per_trade,side,btc_price)

    message = (
        ""
        f"{get_content_title(title)}\n\n"
        f"Value is {formatted_rsi} advice to {side} {'📈' if side=='BUY' else '📉'} \n"
        f"{'Buying' if side =='BUY' else 'Seling'} price is {format_price(btc_price)}\n"
        f"Take Stoploss  {format_price(stop_loss_price)}\n"
        f"Take Profit  {format_price(take_profit_price)}\n"
        f"\n"
        f"💲 margin : {format_amt(cost_per_trade)} 💪 x{leverage}\n"
        f"💣 max stoploss : {format_price(calcu_stop_loss(cost_per_trade,side,btc_price))}\n"
        f"Rate SL/TP is {tp_rate}/{tp_rate}\n"
        f"CreateTime  {formatted_time}\n"
    )
    await send(message)
    time_now = datetime.now()
    ord_id = time_now.strftime("%Y%M%d%H%M%S")
    order_data = {
        'orderId': ord_id,
        'symbol': 'BTCUSDT',
        'side': side,
        'price': btc_price,
        'stop-loss': stop_loss_price,
        'take-profit': take_profit_price,
        'leverage': leverage,
        'status': 'open',
        'result': None,
        'indicator': 'RSI',
        'cost': cost_per_trade,
        'desc': 'New order for BTCUSD'
    }
    insert_order(order_data)


async def notification_close_order(type, price):
    global cost_per_trade, sl_rate, tp_rate
    if type == "TP":
        message = (
            "🎉🎉🎉\n\n"
            f"TAKE PROFIT Price : {format_price(price)}\n"
            f"Profit : {format_amt(cost_per_trade*tp_rate)}\n"
            f"\n"  
        )               
    else:
        message = (
            "💣💣\n\n"
            f"STOP LOSS Price : {format_price(price)}\n"  
            f"Lost : {format_amt(cost_per_trade*sl_rate)}\n"  
            f"\n"
        )  
    await send(message)

    params = {
        'status': 'open',
        'symbol': 'BTCUSDT',
    }
    update_fields = {
        "status": "closed",
        "result": type
    }
    update_order(params,update_fields)


async def validate_order(price):
    print(f"price {price} take_profit_price {take_profit_price} stop_loss_price {stop_loss_price} ")
    global is_side_open, isOpenOrder
    if is_side_open == "BUY":
        if price > take_profit_price:
            logger.info(f"CLOSE => {is_side_open} TAKE PROFIT {price}")
            await notification_close_order("TP", price)
            isOpenOrder = False
            return True
        elif price < stop_loss_price:
            logger.info(f"CLOSE => {is_side_open} STOP LOSS {price}")
            await notification_close_order("SL", price)
            isOpenOrder = False
            return True
    elif is_side_open == "SELL":
        if price < take_profit_price : 
            logger.info(f"CLOSE => {is_side_open} TAKE PROFIT {price}")
            await notification_close_order("TP", price)
            isOpenOrder = False
            return True
        if price > stop_loss_price:
            logger.info(f"CLOSE => {is_side_open} STOP LOSS {price}")
            await notification_close_order("SL", price)
            isOpenOrder = False
            return True
    return False


async def main(symbol='BTC/USDT', period=14, interval=60):
    global isOpenOrder, take_profit_price, stop_loss_price, is_side_open
    while True:
        try:
            await asyncio.sleep(interval)
            price_btc = get_current_btc_usdt_price()
            if price_btc is None:
                logger.error(f"E004. Can't get price BTC")
                print(f"Error. Can't get price BTC")
                continue

            if isOpenOrder:
                is_close = await validate_order(price_btc)
                logger.info(f"Alert ! BTC price is {format_price(price_btc)}. Validate order is {is_close}")
                if is_close:
                    isOpenOrder = False
                    take_profit_price = 0
                    stop_loss_price = 0

            else:
                df_1m = fetch_ohlcv(symbol, interval_1m)
                df_1m = calculate_rsi(df_1m, period)
                current_rsi_1m = df_1m['rsi'].iloc[-1]
                k = 30
                if current_rsi_1m < (50-k):
                    is_side_open = "BUY"
                    await new_order(current_rsi_1m,"BUY", price_btc,"RSI1")
                    isOpenOrder = True
                elif current_rsi_1m > (50+k):
                    is_side_open = "SELL"
                    await new_order(current_rsi_1m,"SELL", price_btc,"RSI1")
                    isOpenOrder = True
                message = f"RSI Alert! Current RSI for {symbol} on {interval_1m} is {current_rsi_1m:.2f} price {format_price(price_btc)}"
                logger.info(message)
        except asyncio.CancelledError as e:
            print(f"E006. An error occurred {e}")
            logger.error(f"E006. An error occurred {e}")
            continue
        except Exception as ex:
            print(f"E007.An error occurred {ex}")
            logger.error(f"E007.An error occurred {ex}")
            continue





def notification_device_name():
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        message=(
            f"\n"
            f"🏃‍♂️🏃‍♂️🏃‍♂️💨\n"
            f"Version: {__version__}\n"
            f"Hostname: {hostname}\n"
            f"IP Address: {ip_address}\n"
        )
        asyncio.run(send(message))
    except Exception as e:
        print(f"get info ip error {e}")


def select_oder():
    orders = select_orders_by_status("open")
    if not orders:
        print("select order is empty")
        return True
    elif len(orders) > 1:
        print(f"E005. Data wrong had {len(orders)} order")
        return False
    else:
        order = orders[0]
        global isOpenOrder, take_profit_price, stop_loss_price, is_side_open
        isOpenOrder = True
        is_side_open = order.get('side')
        take_profit_price = order.get('take-profit')
        stop_loss_price = order.get('stop-loss')
        print(f"is_side_open: {is_side_open}")
        print(f"take_profit_price: {take_profit_price}")
        print(f"stop_loss_price: {stop_loss_price}")
        return True


if __name__ == "__main__":
    print("start ...")
    logger.info("\n\n\t===============> BEGIN RUN <===============\n")
    # test_update_order()
    is_valid_order = select_oder()
    if is_valid_order:
        notification_device_name()
        asyncio.run(main())
    else:
        print("... error because open than more one order")


