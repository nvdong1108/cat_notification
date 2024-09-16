

from logger.logger_setup import logger
from binance.client import Client
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from common.constants import *
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)



def sell_futures(symbol, quantity, leverage=1, price=None):
    """
    Hàm để tạo lệnh bán (sell) trên Binance Futures.

    Parameters:
    symbol (str): Cặp giao dịch (ví dụ: 'BTCUSDT').
    quantity (float): Số lượng cần bán (tính theo hợp đồng futures).
    price (float): Giá bán (nếu là lệnh limit, nếu không truyền vào thì mặc định là lệnh market).
    leverage (int): Đòn bẩy sử dụng (mặc định là 1).

    Returns:
    dict: Thông tin phản hồi từ Binance API về lệnh đã đặt.
    """
    try:
        print(f"sell_futures leverage = {leverage}")
        client.futures_change_leverage(symbol=symbol, leverage=leverage)

        if price:
            order = client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce='GTC'
            )
        else:
            order = client.futures_create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )

        print(f"Lệnh bán {quantity} {symbol} đã được đặt thành công.")
        logger.info(f" new sell order success {order}")
        return order

    except Exception as e:
        logger.error(f" An error occurred sell order {e}")
        print(f"Đã xảy ra lỗi khi đặt lệnh bán: {e}")
        return None


def buy_futures(symbol, quantity, leverage= 1, price=None):
    try:
        print(f"buy_futures leverage = {leverage}")
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        if price is None:
            order = client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
        else:
            order = client.futures_create_order(
                symbol=symbol,
                side="BUY",
                type="LIMIT",
                timeInForce="GTC",
                quantity=quantity,
                price=price
            )

        print("Order placed:", order)
        logger.info(f" new buy order success {order}")
        return order

    except Exception as e:
        logger.error(f" An error occurred buy order {e}")
        print("An error occurred:", e)
        return None


def buy_futures_btcusdt(price):
    logger.info(f" new buy order")
    buy_futures("BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE, price)


def sell_futures_btcusdt(price):
    logger.info(f" new sell order")
    sell_futures("BTCUSDT", QUANTITY_PER_TRADE, LEVERAGE,  price)
