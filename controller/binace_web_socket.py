
import sys
import os

import config.storage

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import asyncio
from binance import AsyncClient
from binance.client import Client
from binance.streams import BinanceSocketManager
from binance.exceptions import BinanceAPIException
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from config.storage import ShareState
from logger.logger_setup import logger
from controller.binace_controller import handle_stop_market, handle_take_profit

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)


async def process_order_update(order: dict):
    """
    Xử lý cập nhật lệnh từ WebSocket.
    Gửi email thông báo khi có sự kiện quan trọng.
    """
    try:
        if not order:
            print(f"[process_order_update] not had info order from socket do handle")
            logger.error(f"[process_order_update] not had info order from socket do handle")
            return
        logger.info(f"response information order from websocket {order}")
        order_id = order.get('i')  # Order ID
        symbol = order.get('s')  # Symbol
        side = order.get('S')  # SIDE: BUY hoặc SELL
        order_type = order.get('o')  # Order Type
        status = order.get('X')  # Status
        price = order.get('p')  # Price
        avg_price = order.get('ap')  # Average Price
        executed_qty = order.get('z')  # Executed Quantity
        client_order_id = order.get('c')  # Client Order ID


        print(f"Order Update: ID={order_id}, Symbol={symbol}, Side={side}, Type={order_type}, Status={status}, Price={price}, Avg Price={avg_price}, Executed Qty={executed_qty}")

        subject = f"Binance Order Update: {symbol} {side}"
        body = (
            f"Order ID: {order_id}\n"
            f"Symbol: {symbol}\n"
            f"Side: {side}\n"
            f"Type: {order_type}\n"
            f"Status: {status}\n"
            f"Price: {price}\n"
            f"Average Price: {avg_price}\n"
            f"Executed Quantity: {executed_qty}\n"
        )
        print(f" show log {status} and body {body}")

        if ShareState.get_order_id(order_id):
            ShareState.update_order(order_id=order_id, status=status)
            if status == 'NEW':
                print("update info ShareState.status_order = NEW in response from websocket")
                logger.info("update info ShareState.status_order = NEW in response from websocket")
            elif status == 'FILLED':
                order_stop = handle_stop_market(symbol, side, int(price))
                if order_stop:
                    stop_loss_id = order_stop['orderId']
                    ShareState.update_order(order_id=order_id, stop_loss=stop_loss_id)
                    logger.info(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")
                    print(f"stop loss id of order {order_id} is {stop_loss_id} with price {price} + 600")

                order_profit = handle_take_profit(symbol, side, int(price))
                if order_profit:
                    order_profit_id = order_profit['orderId']
                    ShareState.update_order(order_id=order_id, take_profit=order_profit_id)
                    logger.info(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")
                    print(f"take profit id of order {order_id} is {order_profit_id} with price {price} + 600")

            if status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                """ cancel all order stop loss and take profit """
                print(f"Response websocket order Status = {status}")
                logger.info(f"Response websocket order Status = {status}")
                ShareState.reset_order()

        elif ShareState.get_order_stop_loss_id(order_id):
            print(f"Response order stop loss with order_id {order_id}")
        elif ShareState.get_order_take_profit_id(order_id):
            print(f"Response order take profit with order_id {order_id}")
        else:
            print(f"Order_id {order_id} not in ShareState.orders")

    except Exception as e:
        print(f"Error processing order update: {e}")


async def handle_socket_message(msg: dict):
    """
    Xử lý thông điệp nhận được từ WebSocket.
    """
    try:
        event_type = msg.get('e')
        if event_type == 'ORDER_TRADE_UPDATE':
            order = msg.get('o')
            await process_order_update(order)
    except Exception as e:
        print(f"Error handling socket message: {e}")


async def start_websocket():
    """
    Bắt đầu kết nối tới Binance User Data Stream WebSocket.
    """
    client = None
    try:
        client = await AsyncClient.create(BINANCE_API_KEY, BINANCE_API_SECRET)

        bsm = BinanceSocketManager(client)
        listen_key_response = await client.futures_stream_get_listen_key()
        if isinstance(listen_key_response, dict):
            listen_key = listen_key_response.get('listenKey')
        elif isinstance(listen_key_response, str):
            listen_key = listen_key_response
        else:
            print(f"Unexpected listen_key_response type: {type(listen_key_response)}")
            return
        print(f"Listen Key: {listen_key}")
        if not listen_key:
            print("Failed to obtain listen key.")
            return

        async with bsm.futures_user_socket() as stream:
            print("Connected to User Data Stream WebSocket.")
            while True:
                msg = await stream.recv()
                await handle_socket_message(msg)

    except BinanceAPIException as e:
        print(f"Binance API Exception: {e}")
    except Exception as e:
        print(f"Unexpected error in WebSocket: {e}")
    finally:
        if client:
            await client.close_connection()


if __name__ == "__main__":
    try:
        print("Starting Binance WebSocket...")
        asyncio.run(start_websocket())
    except KeyboardInterrupt:
        print("WebSocket stopped by user.")
    except Exception as e:
        print(f"Error running WebSocket: {e}")
