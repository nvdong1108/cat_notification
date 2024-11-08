from config.storage import ShareState
from controller.binace.send_api import get_info_order, get_position_information
from logger.logger_setup import logger
from logger.print_until import print_time


def check_order_status_new():
    """
    1. get status order .
    - new : continutetion
    - filled :
    . check position :
    if position :
        update storage
    else
        reset storage

    :return:
    """
    if ShareState.get_order_status() != 'NEW':
        "don't care"
        return False

    order = get_info_order(ShareState.get_order_id())
    if order is None:
        "don't get history of order_id"
        return False

    status = order['status']
    print(f"order status =  {status}")

    if status in ['NEW', 'PARTIALLY_FILLED']:
        "do right, don't care"
        return False

    position = get_position_information()
    if position is None:
        mess_error = "Error data : status = NEW but not order, Reset ShareState order"
        logger.error(f"{mess_error}")
        print_time(f"{mess_error}")
        ShareState.reset_order()
        return False

    if len(position) > 0:
        """update status order manual"""
        ShareState.update_order(order_id=ShareState.get_order_id(), status="FILLED")
        print_time(f"Update status order at check_order_status_new success")
        logger.info(f"Update status order at check_order_status_new success")




