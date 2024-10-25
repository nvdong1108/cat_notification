
from logger.print_until import print_time
from logger.logger_setup import logger
from config.storage import ShareState
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from binance.client import Client
from binance.exceptions import BinanceAPIException

from common.constants import *
from controller.binace.send_api import open_stop_market


client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


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
            condition_change_loss = ShareState.get_condition_change_loss() + 0.5
            ShareState.update_order(order_id=order_id, stop_loss=stop_loss_id, condition_change_loss=condition_change_loss)

            print_time(f"*** end handle_change_stop_loss: success")
            logger.info(f"*** end handle_change_stop_loss: success")
        except BinanceAPIException as e:
            message = f"Error at handle_change_stop_loss: canceling stop loss order: {e}"
            logger.error(message)
            print_time(message)
        return None


def handle_change_profit(mark_price):
    """
    1. check condition change
    2. cancel profit current
    3. open new profit
    4. update id profit new
    :return:
    """

    return True



