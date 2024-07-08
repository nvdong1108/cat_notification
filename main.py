import schedule # type: ignore
import time
import socket
from version import __version__
from controller.indicator.rsi_fetcher import open_ord_1m
from controller.telegram import send as send_group_telegram


def before():
    try:
        print(f"begin task RSI 1m ")
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        message=(
                f"\n"
                f"🏃‍♂️🏃‍♂️🏃‍♂️💨\n" 
                f"Vesion : {__version__}\n"    
                f"Hostname : {hostname}\n"
                f"IP Address : {ip_address}\n"
                )
                
        send_group_telegram(message)
    except Exception as e:
       print(f"get info ip error {e}")    


def task1():
    print("task1")
    open_ord_1m()


schedule.every(30).seconds.do(task1)


if __name__ == "__main__":
    print("start ...")
    before()
    while True:
         schedule.run_pending()
         time.sleep(1)
