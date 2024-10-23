
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import ccxt
import pandas as pd
import ta
import asyncio
import itertools

from logger.print_until import print_time
from  common.date_until import current_time
from tenacity import retry, stop_after_attempt, wait_fixed
from logger.logger_setup import logger
from controller.binace_controller import (buy_futures_btcusdt, sell_futures_btcusdt, fetch_rsi,
                                          check_open_order, get_profit_position, handle_recheck_bug_stop_profit)
from controller.binace_web_socket import start_websocket
from common.calculater_until import *
from config.storage import ShareState



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


async def main(symbol='BTC/USDT', period=14, interval=60):
    """ todo loop """
    three_minutes = 180
    thirty_minutes = 1800
    # ten_minutes = 600
    for count in itertools.count():
        try:
            await asyncio.sleep(interval)

            if count % (thirty_minutes // interval) == 0:
                print_time(f"{ShareState.get_oder_info()}")
                logger.info(f"{ShareState.get_oder_info()}")

            if ShareState.is_none_order():
                current_rsi_1m = fetch_rsi('1m')
                current_rsi_15m = fetch_rsi('15m')
                k = 25
                message = f"*** RSI 1m = {current_rsi_1m}, RSI 15m ={current_rsi_15m}"
                logger.info(message)
                print_time(message)

                if current_rsi_1m < (50-k):
                    buy_futures_btcusdt()
                    continue

                if current_rsi_1m > (50+k):
                    sell_futures_btcusdt()
                    continue

            elif ShareState.is_bug_miss_open_order_stop_loss():
                """create position success but don't create order stop loss """
                handle_recheck_bug_stop_profit()

            elif ShareState.is_bug_miss_open_order_take_profit():
                """create position success but don't create order stop loss """
                handle_recheck_bug_stop_profit()

            elif ShareState.is_handle_price_stop_loss():
                if count % (three_minutes // interval) == 0:
                    get_profit_position()

        except asyncio.CancelledError as e:
            print(f"E006. An error occurred {e}")
            logger.error(f"E006. An error occurred {e}")
            continue
        except Exception as ex:
            print(f"E007.An error occurred {ex}")
            logger.error(f"E007.An error occurred {ex}")
            continue


async def run_all_tasks():
    await asyncio.gather(
        start_websocket(),
        main()
    )


if __name__ == "__main__":
    print("start ...")
    logger.info("\n\n\t===============> BEGIN RUN <===============\n")
    is_valid_order = check_open_order()

    if is_valid_order:
        asyncio.run(run_all_tasks())
    else:
        print("... error because open than more one order")




