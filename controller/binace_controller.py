
import uuid
import threading

import config.config
from logger.logger_setup import logger
from binance.client import Client
import time


from binance.exceptions import BinanceAPIException
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from config.storage import ShareState

from common.constants import *
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


def generate_client_order_id():
    return f"order_{uuid.uuid4()}"


def synchronize_time():
    try:
        server_time = client.get_server_time()
        server_timestamp = server_time['serverTime']
        local_timestamp = int(time.time() * 1000)
        time_offset = server_timestamp - local_timestamp
        client.TIME_OFFSET = time_offset
        logger.info(f"Time has been synchronized. Time offset: {time_offset} ms.")
    except BinanceAPIException as e:
        logger.error(f"Unable to synchronize time: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during time synchronization: {e}")


def periodic_time_sync(interval=120):
    while True:
        try:
            synchronize_time()
        except Exception as e:
            logger.error(f"Error while synchronizing time: {e}")
        time.sleep(interval)


sync_thread = threading.Thread(target=periodic_time_sync, args=(60,), daemon=True)
sync_thread.start()


def round_price(price):
    return int(price)


def check_open_order():
    try:
        positions = client.futures_position_information()
        open_positions = [position for position in positions if float(position['positionAmt']) != 0]

        if open_positions:
            if len(open_positions) > 1:
                print("Error: Multiple open positions detected!")
                logger.error(f"Error: Multiple open positions detected {len(open_positions)} !")
                return False

            for position in open_positions:
                symbol = position['symbol']
                side = 'BUY' if float(position['positionAmt']) > 0 else 'SELL'
                entry_price = position['entryPrice']
                status = 'FILLED'

                print(f"entryPrice: {entry_price} - side {side} ")
                main_order = None
                stop_loss_order = None
                take_profit_order = None
                if symbol != 'BTCUSDT':
                    logger.error(f"ignore order {symbol} ")
                    continue

                orders = client.futures_get_open_orders(symbol='BTCUSDT')
                for order in orders:
                    order_type = order.get('type')
                    print(f" order_type = {order_type}")
                    if order_type == 'STOP_MARKET':
                        stop_loss_order = order
                    elif order_type in ['TAKE_PROFIT_LIMIT', 'TAKE_PROFIT_MARKET', 'TAKE_PROFIT']:
                        take_profit_order = order
                    elif order_type == 'LIMIT':
                        main_order = order

                if main_order:
                    order_id = main_order['orderId']
                    ShareState.set_order(order_id, side, status)

                    if stop_loss_order:
                        order_stop_loss_id = stop_loss_order['orderId']
                        ShareState.update_order(order_id=order_id, stop_loss=order_stop_loss_id)
                        print(f"Stop loss exists for {symbol}: Order ID = {order_stop_loss_id}")

                    if take_profit_order:
                        order_profit_id = take_profit_order['orderId']
                        ShareState.update_order(order_id=order_id, take_profit=order_profit_id)
                        print(f"Take profit exists for {symbol}: Order ID = {order_profit_id}")

                    print(f"Info order {ShareState.order}")
                else:
                    print("WHY 1 ? had position open order_type not LIMIT")

            return True
        else:
            """check order open
            """
            orders = client.futures_get_open_orders(symbol='BTCUSDT')
            for order in orders:
                print(f"order = {order} ")
                order_type = order.get('type')

                print(f"order type of order is {order_type}")

                if order_type == 'STOP_MARKET':
                    """todo cancel
                    """
                    cancel_response = client.futures_cancel_order(symbol='BTCUSDT', orderId=order['orderId'])
                    print(f"cancel order stop market success because not position open {cancel_response}")
                    logger.info(f"cancel order stop market success because not position open {cancel_response}")
                elif order_type == 'TAKE_PROFIT' or order_type == 'TAKE_PROFIT_LIMIT':
                    cancel_response = client.futures_cancel_order(symbol='BTCUSDT', orderId=order['orderId'])
                    print(f"cancel order take profit success because not position open {cancel_response}")
                    logger.info(f"cancel order take profit success because not position open {cancel_response}")

            ShareState.reset_order()
            print(f"not had order open")
            return True

    except BinanceAPIException as e:
        print(f"Error fetching open positions: {e}")
        logger.error(f"Error fetching open positions: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        return False


def check_order_status(order_id):
    try:
        return client.futures_get_order(symbol="BTCUSDT", orderId=order_id)
    except BinanceAPIException as e:
        logger.error(f"Error ERROR_STATUS_1 when check status order: {e}")
        return None
    except Exception as e:
        logger.error(f" Error ERROR_STATUS_2 when check status order: {e}")
        return None


def open_stop_market(stop_side, quantity, stop_price, reduce_only=True):
    try:
        stop_order = client.futures_create_order(
            symbol='BTCUSDT',
            side=stop_side,
            type="STOP_MARKET",
            quantity=quantity,
            stopPrice=str(stop_price),
            closePosition=True,
            reduceOnly=reduce_only
        )

        logger.info(f"Stop Loss Order placed: {stop_order}")
        print(f"Stop Loss Order placed: {stop_order}")
        return stop_order

    except BinanceAPIException as e:
        logger.error(f"Error placing Stop Loss order: {e}")
        print(f"Error placing Stop Loss order: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error placing Stop Loss order: {e}")
        print(f"Unexpected error placing Stop Loss order: {e}")
        return None


async def create_take_profit_order(side, quantity, takeprofit_price):
    """
    Tạo lệnh take profit.
    """
    try:
        takeprofit_response = await client.futures_create_order(
            symbol='BTCUSDT',
            side=side,
            type='TAKE_PROFIT',
            stopPrice=takeprofit_price,
            quantity=quantity,
            reduceOnly=True,
        )
        return takeprofit_response

    except BinanceAPIException as e:
        print(f"Binance API Exception: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error creating take profit order: {e}")
        return None


def open_orders(side,  symbol, quantity, leverage=1, price=None):
    try:
        print(f"buy_futures leverage = {leverage}")
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        if price is None:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        else:
            if price is not None:
                price = round_price(price)
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=str(price)
            )

        order_id = order['orderId']
        order_status = order['status']
        ShareState.set_order(order_id, order_status, side)


        print("Order placed:", order)
        logger.info(f" orderId {order}")
        logger.info(f" end new orders on binance")
        return order

    except Exception as e:
        logger.error(f" An error occurred buy order {e}")
        print("An error occurred:", e)
        return None


def buy_futures_btcusdt(price):
    logger.info(f" new buy order")
    synchronize_time()
    return open_orders("BUY", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE, price)


def sell_futures_btcusdt(price):
    logger.info(f" new sell order")
    synchronize_time()
    return open_orders("SELL", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE, price)


def handle_stop_market(symbol, side, price):
    if symbol != 'BTCUSDT':
        return None
    order_stop = None
    if side == 'SELL':
        price = price + 600
        order_stop = open_stop_market('BUY', QUANTITY_PER_TRADE, price)
    elif side == 'BUY':
        price = price - 600
        order_stop = open_stop_market('SELL', QUANTITY_PER_TRADE, price)
    else:
        print(f"Error: Side handle stop market order wrong side = {side}")

    logger.info(f"handle stop market order success with info order = {order_stop}")
    return order_stop


def handle_take_profit(symbol, side, price):
    if symbol != 'BTCUSDT':
        return None
    order_stop = None
    if side == 'SELL':
        price = price - 660
        order_stop = create_take_profit_order('BUY',  QUANTITY_PER_TRADE, price)
    elif side == 'BUY':
        price = price + 660
        order_stop = create_take_profit_order('SELL', QUANTITY_PER_TRADE, price)
    else:
        print(f"Error: Side handle stop market order wrong side = {side}")

    logger.info(f"handle stop market order success with info order = {order_stop}")
    return order_stop


