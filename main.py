import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
import asyncio
from logger.logger_setup import logger
from controller.binace_controller import check_open_order
from controller.binace_web_socket import start_websocket
from controller.rsi_fetcher import main


async def run_all_tasks():
    await asyncio.gather(
        start_websocket(),
        main()
    )


if __name__ == "__main__":
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("start ...")
    logger.info("\n\n\t===============> BEGIN RUN <===============\n")
    is_valid_order = check_open_order()

    if is_valid_order:
        asyncio.run(run_all_tasks())
    else:
        print("... error because open than more one order")


