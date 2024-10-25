
from http.client import RemoteDisconnected

from logger.print_until import print_time
from logger.logger_setup import logger
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET
from binance.client import Client
from binance.exceptions import BinanceAPIException
import time

client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
listen_key = client.futures_stream_get_listen_key()


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

