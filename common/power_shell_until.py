import subprocess
import schedule
import time
from datetime import datetime
from logger.logger_setup import logger
from logger.print_until import print_time
import asyncio


async def sync_now():
    try:
        print_time(f"*** Syncing system time at {datetime.now()}...")

        subprocess.run("powershell.exe w32tm /resync", check=True, shell=True)
        mess2 = "*** System time synchronized successfully."
        print_time(mess2)
        logger.info(mess2)

    except subprocess.CalledProcessError as e:
        mess = f"*** Error at sync_now: Failed to synchronize system time: {e}"
        print_time(mess)
        logger.error(mess)


async def schedule_sync():
    try:
        print("here go")
        await sync_now()
        schedule.every(4).hours.do(lambda: asyncio.create_task(sync_now()))
        while True:
            schedule.run_pending()
            await asyncio.sleep(60)
    except Exception as e:
        print_time(f"Error at schedule_sync:  {e}")