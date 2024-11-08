import time

from logger.logger_setup import logger
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from binance.client import Client
from binance.exceptions import BinanceAPIException
from controller.binace.time_server import synchronize_time
from config.storage import ShareState
from logger.print_until import print_time
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


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
            price = int(price)
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
        take_profit_response = client.futures_create_order(
            symbol='BTCUSDT',
            side=side,
            type='TAKE_PROFIT_MARKET',
            timeInForce='GTC',
            stopPrice=str(price),
            closePosition=True,
            timestamp=synchronize_time()
        )
        logger.info(f"\n*** CREATE TAKE PROFIT SUCCESS: {take_profit_response}")
        print(f"\n*** CREATE TAKE PROFIt SUCCESS")
        return take_profit_response

    except BinanceAPIException as e:
        print(f"Error: Create_take_profit_order Binance API Exception: {e}")
        logger.error(f"Error: Create_take_profit_order Binance API Exception: {e}")
        return None
    except Exception as e:
        print(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        logger.error(f"Error: Create_take_profit_order Unexpected error creating take profit order: {e}")
        return None


def get_position_information(retries=3):
    """
    :return:
    """
    while retries > 0:
        try:
            positions = client.futures_position_information(timestamp=synchronize_time(),
                                                        recvWindow=10000)
            open_positions = [position for position in positions if float(position['positionAmt']) != 0]
            return open_positions
        except Exception as e:
            ms = f"Error at get_position_information: retries = {retries} {e}"
            print_time(ms)
            logger.error(ms)
            retries -= 1
            time.sleep(5)
    # call error return -1
    return -1


def get_info_order(order_id):
    order = client.futures_get_order(
        symbol='BTCUSDT',
        orderId=order_id
    )
    return order

