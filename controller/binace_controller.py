
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


def get_latest_orders(symbol, side):
    try:
        orders = client.futures_get_all_orders(symbol=symbol)
        if side:
            orders = [order for order in orders if order['side'] == side]

        sorted_orders = sorted(orders, key=lambda x: x['time'], reverse=True)
        if sorted_orders:
            latest_order = sorted_orders[0]
            order_id = latest_order['orderId']
            order_time = latest_order['time']
            order_type = latest_order['type']
            order_status = latest_order['status']
            print(f"Order ID: {order_id}, Time: {order_time}, Type: {order_type}, Status: {order_status}, Side: {latest_order['side']}")
            return latest_order

        return None

    except BinanceAPIException as e:
        logger.error(f"Binance API Exception while fetching orders: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching orders: {e}")
        return None


def check_open_order():
    try:
        positions = client.futures_position_information()
        open_positions = [position for position in positions if float(position['positionAmt']) != 0]

        if open_positions:
            print(f"open_positions = {open_positions}")
            if len(open_positions) > 1:
                print("Error: Multiple open positions detected!")
                logger.error(f"Error: Multiple open positions detected {len(open_positions)} !")
                return False

            for position in open_positions:
                symbol = position['symbol']
                side = 'BUY' if float(position['positionAmt']) > 0 else 'SELL'
                entry_price = position['entryPrice']
                status = 'FILLED'

                print(f"Begin check_open_order: entryPrice: {entry_price} - side {side} ")
                main_order = None
                stop_loss_order = None
                take_profit_order = None
                if symbol != 'BTCUSDT':
                    logger.error(f"ignore order {symbol} ")
                    continue

                orders_open_filled = get_latest_orders('BTCUSDT', side)

                if orders_open_filled is None:
                    print("Error check_open_order. not get history position ")
                    return False

                order_id = orders_open_filled['orderId']
                ShareState.set_order(order_id, side, status)

                orders = client.futures_get_open_orders(symbol='BTCUSDT')

                for order in orders:
                    order_type = order.get('type')
                    print(f" order_type = {order_type}")
                    if order_type == 'STOP_MARKET':
                        stop_loss_order = order
                    elif order_type in ['TAKE_PROFIT_LIMIT', 'TAKE_PROFIT_MARKET', 'TAKE_PROFIT']:
                        take_profit_order = order
                    elif order_type == 'LIMIT':
                        print("begin check order: had order_type = LIMIT, warning, check order had stop or profit")

                if stop_loss_order:
                    order_stop_loss_id = stop_loss_order['orderId']
                    ShareState.update_order(order_id=order_id, stop_loss=order_stop_loss_id)
                    print(f"Stop loss exists for {symbol}: Order ID = {order_stop_loss_id}")

                if take_profit_order:
                    order_profit_id = take_profit_order['orderId']
                    ShareState.update_order(order_id=order_id, take_profit=order_profit_id)
                    print(f"Take profit exists for {symbol}: Order ID = {order_profit_id}")

                    print(f"Info order {ShareState.order}")

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
            closePosition=True
        )

        logger.info(f"Create order stop loss success : {stop_order}")
        print(f"Create order stop loss success : {stop_order}")
        return stop_order

    except BinanceAPIException as e:
        logger.error(f"Error: open_stop_market placing Stop Loss order: {e}")
        print(f"Error: open_stop_market placing Stop Loss order: {e}")
        return None
    except Exception as e:
        logger.error(f"Error: open_stop_market Unexpected error placing Stop Loss order: {e}")
        print(f"Error: open_stop_market Unexpected error placing Stop Loss order: {e}")
        return None


def create_take_profit_order(side, quantity, takeprofit_price):
    """
    Tạo lệnh take profit.
    """
    try:
        takeprofit_response = client.futures_create_order(
            symbol='BTCUSDT',
            side=side,
            type='TAKE_PROFIT_LIMIT',
            stopPrice=takeprofit_price,
            quantity=quantity,
            reduceOnly=True,
        )
        logger.info(f"Create Take profir success: {takeprofit_response}")
        print(f"Create Take profir success: {takeprofit_response}")
        return takeprofit_response

    except BinanceAPIException as e:
        print(f"Error: Create_take_profit_order Binance API Exception: {e}")
        logger.error(f"Error: Create_take_profit_order Binance API Exception: {e}")
        return None
    except Exception as e:
        print(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        logger.error(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        return None


def open_orders(side,  symbol, quantity, leverage=1, price=None):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        if price is None:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        else:
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
        ShareState.set_order(order_id, side, order_status)

        print(f"Open new order Success {ShareState.order}")
        logger.info(f"Open new order Success {ShareState.order}")
        return order

    except Exception as e:
        logger.error(f" An error occurred buy order {e}")
        print("An error occurred:", e)
        return None


def buy_futures_btcusdt(price):
    logger.info(f"===> NEW BUY order with price {price}")
    synchronize_time()
    return open_orders("BUY", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE, price)


def sell_futures_btcusdt(price):
    logger.info(f"===> NEW SELL order with price {price}")
    synchronize_time()
    return open_orders("SELL", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE, price)


def handle_stop_market(symbol, side, price):
    if symbol != 'BTCUSDT':
        return None
    order_stop = None

    if side == 'SELL':
        price = int(price) + 600
        order_stop = open_stop_market('BUY', QUANTITY_PER_TRADE, price)
    elif side == 'BUY':
        price = int(price) - 600
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
        price = int(price) - 660
        order_stop = create_take_profit_order('BUY',  QUANTITY_PER_TRADE, price)
    elif side == 'BUY':
        price = int(price) + 660
        order_stop = create_take_profit_order('SELL', QUANTITY_PER_TRADE, price)
    else:
        print(f"Error: Side handle stop market order wrong side = {side}")

    logger.info(f"handle handle_take_profit order success with info order = {order_stop}")
    return order_stop


