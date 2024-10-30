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
from tenacity import retry, stop_after_attempt, wait_fixed
from logger.logger_setup import logger
from controller.binace_controller import (buy_futures_btcusdt, sell_futures_btcusdt,
                                          check_open_order, get_profit_position, handle_recheck_bug_stop_profit)
from controller.binace.indicator import fetch_rsi
from controller.binace_web_socket import start_websocket
from config.storage import ShareState


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

            if ShareState.is_true_none_order():
                current_rsi_1m = fetch_rsi('1m')
                current_rsi_5m = fetch_rsi('5m')
                current_rsi_15m = fetch_rsi('15m')
                k = 25
                message = f"*** RSI 1m = {current_rsi_1m}, 5m ={current_rsi_5m}, 15m ={current_rsi_15m}"
                logger.info(message)
                print_time(message)

                if current_rsi_1m < (50-k):
                    buy_futures_btcusdt()
                    continue

                if current_rsi_1m > (50+k):
                    sell_futures_btcusdt()
                    continue

            elif ShareState.is_true_bug_miss_open_order_stop_loss():
                """create position success but don't create order stop loss """
                handle_recheck_bug_stop_profit()

            elif ShareState.is_true_bug_miss_open_order_take_profit():
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
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("start ...")
    logger.info("\n\n\t===============> BEGIN RUN <===============\n")
    is_valid_order = check_open_order()

    if is_valid_order:
        asyncio.run(run_all_tasks())
    else:
        print("... error because open than more one order")





