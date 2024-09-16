
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import ccxt
import pandas as pd
import ta
import asyncio

from common.format_until import format_price, format_amt
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from controller.telegram.tetegram_controller import send, notification_device_name, get_content_title
from controller.telegram.tetegram_controller import notification_stop_loss_order, notification_take_profit_order
from logger.logger_setup import logger
from config.mongoDB import insert_order, update_order, select_orders_by_status
from controller.binace_controller import buy_futures_btcusdt, sell_futures_btcusdt
from common.constants import *
from common.calculater_until import *


isOpenOrder = False
is_side_open = ""
stop_loss_price = 0
take_profit_price = 0
btc_usdt_price = 0
cost_per_trade = 0


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


def new_order(rsi, side, btc_price, title):
    logger.info(f"=========== NEW ORDER {side} ===========")
    global take_profit_price, stop_loss_price, cost_per_trade
    
    formatted_rsi = f"{rsi:.2f}"
    current_time = datetime.now()
    formatted_time = current_time.strftime("%Y/%m/%d %H:%M:%S")
    cost_per_trade = QUANTITY_PER_TRADE * btc_price / LEVERAGE
    stop_loss_price = calcu_tk_stop_loss(cost_per_trade, side, btc_price)
    take_profit_price = calcu_take_profit(cost_per_trade, side, btc_price)

    message = (
        ""
        f"{get_content_title(title)}\n\n"
        f"Value is {formatted_rsi} advice to {side} {'📈' if side=='BUY' else '📉'} \n"
        f"{'Buying' if side =='BUY' else 'Selling'} price is {format_price(btc_price)}\n"
        f"Take Stoploss  {format_price(stop_loss_price)}\n"
        f"Take Profit  {format_price(take_profit_price)}\n"
        f"\n"
        f"💲 margin : {format_amt(cost_per_trade)} 💪 x{LEVERAGE}\n"
        f"💣 max stoploss : {format_price(calcu_stop_loss(side, btc_price))}\n"
        f"Rate SL/TP is {TP_RATE}/{TP_RATE}\n"
        f"CreateTime  {formatted_time}\n"
    )
    send(message)
    time_now = datetime.now()
    ord_id = time_now.strftime("%Y%M%d%H%M%S")
    order_data = {
        'orderId': ord_id,
        'symbol': 'BTCUSDT',
        'side': side,
        'price': btc_price,
        'stop-loss': stop_loss_price,
        'take-profit': take_profit_price,
        'leverage': LEVERAGE,
        'status': 'open',
        'result': None,
        'indicator': 'RSI',
        'cost': cost_per_trade,
        'desc': 'New order for BTCUSDT'
    }
    insert_order(order_data)


async def validate_order(price):
    print(f"price {price} take_profit_price {take_profit_price} stop_loss_price {stop_loss_price} ")
    global is_side_open, isOpenOrder
    global cost_per_trade
    if is_side_open == "BUY":
        if price > take_profit_price:
            logger.info(f"CLOSE => {is_side_open} TAKE PROFIT {price}")
            notification_take_profit_order(price, cost_per_trade*TP_RATE)
            update_order(type)
            isOpenOrder = False
            return True
        elif price < stop_loss_price:
            logger.info(f"CLOSE => {is_side_open} STOP LOSS {price}")
            notification_stop_loss_order(price, cost_per_trade*SL_RATE)
            update_order(type)
            isOpenOrder = False
            return True
    elif is_side_open == "SELL":
        if price < take_profit_price:
            logger.info(f"CLOSE => {is_side_open} TAKE PROFIT {price}")
            notification_take_profit_order(price, cost_per_trade*TP_RATE)
            update_order(type)
            isOpenOrder = False
            return True
        if price > stop_loss_price:
            logger.info(f"CLOSE => {is_side_open} STOP LOSS {price}")
            notification_stop_loss_order(price, cost_per_trade*SL_RATE)
            update_order(type)
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
                df_1m = fetch_ohlcv(symbol, INTERVAL_1M)
                df_1m = calculate_rsi(df_1m, period)
                current_rsi_1m = df_1m['rsi'].iloc[-1]
                k = 2
                if current_rsi_1m < (50-k):
                    is_side_open = "BUY"
                    buy_futures_btcusdt(price_btc)
                    new_order(current_rsi_1m,"BUY", price_btc,"RSI1")
                    isOpenOrder = True
                elif current_rsi_1m > (50+k):
                    is_side_open = "SELL"
                    sell_futures_btcusdt(price_btc)
                    new_order(current_rsi_1m,"SELL", price_btc,"RSI1")
                    isOpenOrder = True
                message = f"RSI Alert! Current RSI for {symbol} on {INTERVAL_1M} is {current_rsi_1m:.2f} price {format_price(price_btc)}"
                logger.info(message)
        except asyncio.CancelledError as e:
            print(f"E006. An error occurred {e}")
            logger.error(f"E006. An error occurred {e}")
            continue
        except Exception as ex:
            print(f"E007.An error occurred {ex}")
            logger.error(f"E007.An error occurred {ex}")
            continue


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


