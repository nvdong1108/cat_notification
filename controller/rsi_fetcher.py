import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import asyncio
import itertools

from logger.print_until import print_time
from logger.logger_setup import logger
from controller.binace_controller import (buy_futures_btcusdt, sell_futures_btcusdt,
                                          get_profit_position, handle_recheck_bug_stop_profit)
from controller.binace.indicator import fetch_rsi, fetch_indicators
from config.storage import ShareState
from controller.binace.recheck_order import check_order_status_new

async def main(symbol='BTC/USDT', period=14, interval=60):
    """ todo loop """
    three_minutes = 180
    thirty_minutes = 1800
    print_time(f"running main")
    # ten_minutes = 600
    for count in itertools.count():
        try:
            await asyncio.sleep(interval)

            if count % (thirty_minutes // interval) == 0:
                print_time(f"{ShareState.get_oder_info()}")
                logger.info(f"{ShareState.get_oder_info()}")

            if ShareState.is_true_none_order():
                # current_rsi_1m = fetch_rsi('1m')
                current_rsi_5m, max_rsi5m, min_rsi_5m = fetch_rsi('5m')
                current_rsi_15m = fetch_rsi('15m')
                price, rsi_1m, max, min = fetch_rsi('1m')
                k = 25
                message = f"*** price = {price}, RSI 1m = {rsi_1m}, max = {max}, min = {min}, 5m ={current_rsi_5m}, 15m ={current_rsi_15m}"
                logger.info(message)
                print_time(message)

                if rsi_1m < (50-k):
                    if rsi_1m < (max - 3):
                        buy_futures_btcusdt()
                    else:
                        mess = f"waiting =============> "
                        print()
                    continue

                if rsi_1m > (50+k):
                    sell_futures_btcusdt()
                    continue

            elif ShareState.get_order_status() == 'NEW':
                """fix bug websocket change status new -> filled don't update status"""
                print_time(f"{ShareState.get_oder_info()}")
                check_order_status_new()

            elif ShareState.is_true_bug_miss_open_order_stop_loss():
                """create position success but don't create order stop loss """
                mess = "*** Position  not open STOP_LOSS , begin recheck position"
                print_time(mess)
                logger.info(mess)
                handle_recheck_bug_stop_profit()

            elif ShareState.is_true_bug_miss_open_order_take_profit():
                """create position success but don't create order stop loss """
                mess = "*** Position  not open profit, begin recheck position"
                print_time(mess)
                logger.info(mess)
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








