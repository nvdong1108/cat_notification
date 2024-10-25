
from common.format_until import format_percent, format_amt
from logger.logger_setup import logger

from controller.binace.time_server import synchronize_time
from controller.binace.send_api import create_take_profit_order, open_stop_market, open_orders
from config.storage import ShareState
from common.constants import *

from logger.print_until import print_time
from requests import Session
from binance.exceptions import BinanceAPIException

from binance.client import Client
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET

from controller.binace.change_order import handle_change_stop_loss, handle_change_profit

session = Session()
session.timeout = 20

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


def get_latest_orders(symbol, side):
    try:
        orders = client.futures_get_all_orders(symbol=symbol)
        if side:
            orders = [order for order in orders if order['side'] == side]

        sorted_orders = sorted(orders, key=lambda x: x['time'], reverse=True)
        if sorted_orders:
            latest_order = sorted_orders[0]
            return latest_order

        return None

    except BinanceAPIException as e:
        logger.error(f"Binance API Exception while fetching orders: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error while fetching orders: {e}")
        return None


def get_position_information():
    """
    :return:
    """
    positions = client.futures_position_information(timestamp=synchronize_time())
    open_positions = [position for position in positions if float(position['positionAmt']) != 0]
    return open_positions


def get_profit_position():
    try:
        open_positions = get_position_information()
        if open_positions:
            if len(open_positions) > 1:
                print("Error: Multiple open positions detected!")
                logger.error(f"Error: Multiple open positions detected {len(open_positions)} !")
                return False
            amt_profit = float(open_positions[0]['unRealizedProfit'])
            total_amt = float(open_positions[0]['isolatedWallet'])
            mark_price = round(float(open_positions[0]['markPrice']), 2)
            profit_percentage = (amt_profit / total_amt) * 100
            if amt_profit > ShareState.get_condition_change_loss():
                """ change stop loss"""
                print_time("todo handle_change_stop_loss")
                logger.info("todo handle_change_stop_loss")
                # handle_change_stop_loss(mark_price)
                # handle_change_profit(mark_price)

            message = f"*** POSITIONS profit {format_amt(amt_profit)} percentage is {format_percent(profit_percentage)} "
            print_time(message)
            logger.info(message)

    except Exception as e:
        ms = f"Error at get_profit_position: {e}"
        print_time(ms)
        logger.error(ms)


def check_open_order():
    try:

        open_positions = get_position_information()
        print("****************** goto *********************** ")
        if open_positions:
            if len(open_positions) > 1:
                print("Error: Multiple open positions detected!")
                logger.error(f"Error: Multiple open positions detected {len(open_positions)} !")
                return False

            for position in open_positions:
                symbol = position['symbol']
                side = 'BUY' if float(position['positionAmt']) > 0 else 'SELL'
                status = 'FILLED'

                stop_loss_order = None
                take_profit_order = None
                if symbol != 'BTCUSDT':
                    logger.error(f"ignore order {symbol} ")
                    continue

                orders_open_filled = get_latest_orders('BTCUSDT', side)

                if orders_open_filled is None:
                    print("Error check_open_order. not get history position ")
                    logger.error("Error check_open_order. not get history position ")
                    return False

                order_id = orders_open_filled['orderId']
                ShareState.set_order(order_id, side, status)

                orders = client.futures_get_open_orders(symbol='BTCUSDT')

                for order in orders:
                    order_type = order.get('type')
                    if order_type == 'STOP_MARKET':
                        stop_loss_order = order
                    elif order_type in ['TAKE_PROFIT_LIMIT', 'TAKE_PROFIT_MARKET', 'TAKE_PROFIT']:
                        take_profit_order = order
                    elif order_type == 'LIMIT':
                        print("WARNING: a position already exists, but an order with type LIMIT is still being opened.")
                        logger.warn("WARNING: a position already exists, but an order with type LIMIT is still being opened.")

                if stop_loss_order:
                    order_stop_loss_id = stop_loss_order['orderId']
                    ShareState.update_order(order_id=order_id, stop_loss=order_stop_loss_id)

                if take_profit_order:
                    order_profit_id = take_profit_order['orderId']
                    ShareState.update_order(order_id=order_id, take_profit=order_profit_id)

        else:
            """check order open
            """
            orders = client.futures_get_open_orders(symbol='BTCUSDT')
            count_order_type_limit = 0
            for order in orders:
                order_type = order.get('type')
                if order_type == 'STOP_MARKET':
                    """todo cancel
                    """
                    cancel_response = client.futures_cancel_order(symbol='BTCUSDT', orderId=order['orderId'])
                    print(f"cancel order stop market success because not position open")
                    logger.info(f"cancel order stop market success because not position open {cancel_response}")

                elif order_type == 'TAKE_PROFIT_MARKET' or order_type == 'TAKE_PROFIT_LIMIT':
                    cancel_response = client.futures_cancel_order(symbol='BTCUSDT', orderId=order['orderId'])
                    print(f"cancel order take profit success because not position open")
                    logger.info(f"cancel order take profit success because not position open {cancel_response}")

                elif order_type == 'LIMIT':
                    count_order_type_limit += 1
                    print(f"Had order open Type LIMIT this is order waiting entry Price")
                    logger.info(f"Had order open Type LIMIT this is order waiting entry Price ")
                    if count_order_type_limit < 2:
                        order_id = order.get('orderId')
                        status = order.get('status')
                        side = order.get('side')
                        ShareState.set_order(order_id, side, status)
                    else:
                        print(f"WARNING: ################## had {count_order_type_limit} order open LIMIT ##################")
                        logger.warn(f"WARNING: ################## had {count_order_type_limit} order open LIMIT ##################")

        print(f"{ShareState.get_oder_info()}\n")
        return True

    except BinanceAPIException as e:
        print(f"Error fetching open positions: {e}")
        logger.error(f"Error fetching open positions: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        return False




def buy_futures_btcusdt():
    synchronize_time()
    return open_orders("BUY", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE)


def sell_futures_btcusdt():
    synchronize_time()
    return open_orders("SELL", "BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE)


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
        price_stop = int(price) - 600
        order_stop = create_take_profit_order('BUY', price_stop)
    elif side == 'BUY':
        price_stop = int(price) + 600
        order_stop = create_take_profit_order('SELL', price_stop)
    else:
        print(f"Error: Side handle stop market order wrong side = {side}")

    logger.info(f"handle handle_take_profit order success with info order = {order_stop}")
    return order_stop


def handle_recheck_bug_stop_profit():
    """
    1. lấy position nếu không có return
    2. lấy open_order
    3. check
    """

    open_positions = get_position_information()
    if open_positions is None or len(open_positions) == 0:
        print("Error: Don't recheck open positions.")
        logger.error("Error: Don't recheck open positions.!")
        return False

    orders_open_filled = get_latest_orders('BTCUSDT', ShareState.get_side())
    if orders_open_filled is None:
        print("Error: Don't get_latest_orders")
        logger.error("Error: get_latest_orders")
        return False
    position = open_positions[0]
    symbol = position['symbol']
    side = 'BUY' if float(position['positionAmt']) > 0 else 'SELL'
    price = float(position.get('entryPrice', 0))
    order_id = orders_open_filled['orderId']

    if ShareState.equals_order_id(order_id):
        orders = client.futures_get_open_orders(symbol='BTCUSDT')

        if orders is None or len(orders) == 0:
            """create stop loss and take profit"""
            order_sp_old = ShareState.get_order_stop_loss_id()
            if order_sp_old is None:
                order_stop = handle_stop_market(symbol, side, int(price))
                if order_stop:
                    stop_loss_id = order_stop['orderId']
                    ShareState.update_order(order_id=order_id, stop_loss=stop_loss_id)
                    logger.info(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")
                    print(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")
                else:
                    print(f"1. Don't Update id stop for position because order_sp_old already exists.")

            order_tp_old = ShareState.get_order_take_profit_id()
            if order_tp_old is None:
                order_profit = handle_take_profit(symbol, side, int(price))
                if order_profit:
                    order_profit_id = order_profit['orderId']
                    ShareState.update_order(order_id=order_id, take_profit=order_profit_id)
                    logger.info(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")
                    print(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")
            else:
                print(f"2. Don't Update id take profit for position because order_tp_old already exists.")

        else:
            order_stop_loss_id = None
            order_take_profit_id = None
            for order in orders:
                order_type = order.get('type')
                if order_type == 'STOP_MARKET':
                    order_stop_loss_id = order['orderId']
                if order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT_LIMIT']:
                    order_take_profit_id = order['orderId']

            if order_stop_loss_id:
                order_sp_old = ShareState.get_order_stop_loss_id()
                if order_sp_old is None:
                    ShareState.update_order(order_id=order_id, stop_loss=order_stop_loss_id)
                else:
                    print(f"3. Don't Update id stop loss for position because order_sp_old already exists.")
            else:
                """create stop loss"""
                order_sp_old = ShareState.get_order_stop_loss_id()
                if order_sp_old:
                    print("WARNING: *** why storage already exists but create open new stop loss")

                order_stop = handle_stop_market(symbol, side, int(price))
                if order_stop:
                    stop_loss_id = order_stop['orderId']
                    ShareState.update_order(order_id=order_id, stop_loss=stop_loss_id)
                    logger.info(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")
                    print(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")

            if order_take_profit_id:
                order_sp_old = ShareState.get_order_take_profit_id()
                if order_sp_old is None:
                    ShareState.update_order(order_id=order_id, take_profit=order_take_profit_id)
                else:
                    print(f"4. Don't Update id take profit for position because order_sp_old already exists.")
            else:
                """create take profit"""
                order_sp_old = ShareState.get_order_take_profit_id()
                if order_sp_old:
                    print("WARNING: *** why storage order take profit already exists but create open new take profit")

                order_profit = handle_take_profit(symbol, side, int(price))
                if order_profit:
                    order_profit_id = order_profit['orderId']
                    ShareState.update_order(order_id=order_id, take_profit=order_profit_id)
                    logger.info(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")
                    print(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")
    else:
        print(f"*** WARNING: GET_LATEST_ORDERS {orders_open_filled} NOT IN ShareState.order")


