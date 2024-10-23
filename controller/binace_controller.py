
import uuid
import threading
from http.client import RemoteDisconnected

from common.format_until import format_percent, format_amt, format_rsi
from logger.logger_setup import logger
from binance.client import Client
import time

import pandas as pd
import pandas_ta as ta

from logger.print_until import print_time
from requests import Session
from binance.exceptions import BinanceAPIException
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from config.storage import ShareState

from common.constants import *

session = Session()
session.timeout = 20

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

listen_key = client.futures_stream_get_listen_key()


def fetch_rsi(interval):

    klines = client.futures_klines(symbol='BTCUSDT', interval=interval, limit='500')
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'number_of_trades',
                                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)

    df['rsi'] = ta.rsi(df['close'], length=14)

    return format_rsi(df['rsi'].iloc[-1])


def get_btcusdt_price():
    try:
        ticker = client.futures_symbol_ticker(symbol="BTCUSDT")
        current_price = float(ticker['price'])
        return current_price
    except Exception as e:
        logger.error(f"Error fetching BTCUSDT price: {e}")
        print("Error fetching BTCUSDT price:", e)
        return None


def generate_client_order_id():
    return f"order_{uuid.uuid4()}"


def synchronize_time():
    try:
        server_time = client.futures_time()
        server_timestamp = server_time['serverTime']
        local_timestamp = int(time.time() * 1000)
        time_offset = server_timestamp - local_timestamp
        client.TIME_OFFSET = time_offset
        print_time(f"Time offset {time_offset}")
        return server_timestamp
    except RemoteDisconnected:
        logger.warning(f"At synchronize_time: Remote server disconnected, retrying...")
        return int(time.time() * 1000)
    except BinanceAPIException as e:
        logger.error(f"At synchronize_time: Unable to synchronize time: {e}")
        return int(time.time() * 1000)
    except Exception as e:
        logger.error(f"At synchronize_time: An unexpected error occurred during time synchronization: {e}")
        return int(time.time() * 1000)


# def periodic_time_sync(interval=120):
#     while True:
#         try:
#             synchronize_time()
#         except Exception as e:
#             logger.error(f"Error while synchronizing time: {e}")
#         time.sleep(interval)


# sync_thread = threading.Thread(target=periodic_time_sync, args=(60,), daemon=True)
# sync_thread.start()


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
            if amt_profit > ShareState.get_target_profit():
                """ change stop loss"""
                handle_change_stop_loss(mark_price)

            message = f"*** POSITIONS profit {format_amt(amt_profit)} percentage is {format_percent(profit_percentage)} "
            print_time(message)
            logger.info(message)

    except Exception as e:
        logger.error(f"Error at get_profit_position {e}")


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

        print(f"\n*** INFO ORDER {ShareState.order}\n")
        return True

    except BinanceAPIException as e:
        print(f"Error fetching open positions: {e}")
        logger.error(f"Error fetching open positions: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        return False


def open_stop_market(stop_side, quantity, stop_price):
    try:
        stop_order = client.futures_create_order(
            symbol='BTCUSDT',
            side=stop_side,
            type="STOP_MARKET",
            quantity=quantity,
            stopPrice=str(stop_price),
            closePosition=True,
            timestamp=synchronize_time()
        )

        logger.info(f"*** CREATE ORDER STOP LOSS SUCCESS {stop_order}")
        print(f"\n*** CREATE ORDER STOP LOSS SUCCESS")
        return stop_order

    except BinanceAPIException as e:
        logger.error(f"Error: open_stop_market placing Stop Loss order: {e}")
        print(f"Error: open_stop_market placing Stop Loss order: {e}")
        return None
    except Exception as e:
        logger.error(f"Error: open_stop_market Unexpected error placing Stop Loss order: {e}")
        print(f"Error: open_stop_market Unexpected error placing Stop Loss order: {e}")
        return None


def create_take_profit_order(side, price):
    """
    Tạo lệnh take profit.
    """
    try:
        takeprofit_response = client.futures_create_order(
            symbol='BTCUSDT',
            side=side,
            type='TAKE_PROFIT_MARKET',
            timeInForce='GTC',
            stopPrice=str(price),
            closePosition=True,
            timestamp=synchronize_time()
        )
        logger.info(f"\n*** CREATE TAKE PROFIT SUCCESS: {takeprofit_response}")
        print(f"\n*** CREATE TAKE PROFIt SUCCESS")
        return takeprofit_response

    except BinanceAPIException as e:
        print(f"Error: Create_take_profit_order Binance API Exception: {e}")
        logger.error(f"Error: Create_take_profit_order Binance API Exception: {e}")
        return None
    except Exception as e:
        print(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        logger.error(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        return None


def open_orders(side,  symbol, quantity, leverage=1):
    try:
        price = None #get_btcusdt_price()
        logger.info(f"\n===> BEGIN OPEN NEW {side} ORDER WITH PRICE {price}")
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        if price is None:
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity,
                timestamp=synchronize_time()
            )
        else:
            price = round_price(price)
            order = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=str(price),
                timestamp=synchronize_time()
            )

        order_id = order['orderId']
        order_status = order['status']
        ShareState.set_order(order_id, side, order_status)
        return order

    except Exception as e:
        logger.error(f"Error: open_orders  An error occurred buy order {e}")
        print("Error: open_orders An error occurred:", e)
        return None


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

    if ShareState.get_order_id(order_id):
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


def handle_change_stop_loss(mark_price):
    print_time(f"*** Begin handle_change_stop_loss {mark_price}")
    logger.info(f"*** Begin handle_change_stop_loss {mark_price}")
    order_id = ShareState.get_order_stop_loss_id()
    side = ShareState.get_side()
    space_price = 600

    order = client.futures_get_order(
        symbol='BTCUSDT',
        orderId=order_id
    )

    if order is None:
        print_time("Không thể lấy thông tin lệnh stop loss")
        logger.error("Không thể lấy thông tin lệnh stop loss")
        return None

    if order:
        if side is None:
            logger.error("Invalid stop_side provided")
            print_time("Invalid stop_side provided")
            return None

        new_stop_price = 0
        side_stop_loss = ''
        if side == 'BUY':
            new_stop_price = mark_price - space_price
            side_stop_loss = 'SELL'
        elif side == 'SELL':
            new_stop_price = mark_price + space_price
            side_stop_loss = 'BUY'

        try:
            if order['status'] in ['NEW', 'PARTIALLY_FILLED']:
                cancel_order = client.futures_cancel_order(symbol='BTCUSDT', orderId=order_id)
                if cancel_order is None:
                    print_time(f"Check again Error at handle_change_stop_loss: cancel order stop loss fail")
                else:
                    logger.info(f"*** CANCEL ORDER SUCCESS {cancel_order}")

            order_stop_new = open_stop_market(side_stop_loss, QUANTITY_PER_TRADE, new_stop_price)
            if order_stop_new is None:
                mess = f"Error at handle_change_stop_loss: open new order stop new fail"
                print_time(mess)
                logger.error(f"{mess}")
                return None

            mess = "change order stop loss success"
            print_time(mess)
            logger.info(f"{mess} order = {order_stop_new}")

            stop_loss_id = order_stop_new['orderId']
            target_profit = ShareState.get_target_profit() + 0.5
            ShareState.update_order(order_id=order_id, stop_loss=stop_loss_id, target_profit=target_profit)

            print_time(f"*** end handle_change_stop_loss: success")
            logger.info(f"*** end handle_change_stop_loss: success")
        except BinanceAPIException as e:
            message = f"Error at handle_change_stop_loss: canceling stop loss order: {e}"
            logger.error(message)
            print_time(message)
        return None

