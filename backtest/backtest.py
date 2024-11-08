import pandas_ta as ta
import pandas as pd
from binance.client import Client
import os
from datetime import datetime
import numpy as np
from datetime import datetime, timedelta, timezone


client = Client('afZzAgNGH5Mq1dEx5fguELTbY4JZ5n9pf5WNfAQu8rWDiPQUjVxho3SHZ2BLiDSx', 'pjaF2LZ6vRIcpEQMcycGWFIwsc0ctdwRRda7tJ5um22OHR1ztjXX4JwbLF26dRyN')

win = 0
loss = 0
price_target = 600


def format_rsi(rsi):
    if rsi is None or pd.isna(rsi):
        return None
    if isinstance(rsi,float):
        return int(rsi)
    return int(rsi)


def convert_to_utc_plus_7(utc_time):
    utc_time = datetime.strptime(utc_time, '%Y-%m-%d %H:%M:%S %Z')
    utc_plus_7 = utc_time + timedelta(hours=7)
    return utc_plus_7.strftime('%Y-%m-%d %H:%M:%S')


def format_timestamp(timestamp):
    try:
        if isinstance(timestamp, (int, np.integer)):
            timestamp = datetime.fromtimestamp(timestamp / 1000)  
        
        formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        return formatted_time
    except Exception as e:
        return f"Error formatting timestamp: {e}"

def log_time():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def evaluate_signal(df, start_index, signal_type, initial_price, file):
    global win, loss, price_target

    price_stop  = 0

    for i in range(start_index + 1, len(df)):
        current_price =int(df['close'].iloc[i])
        rsi = int(df['rsi'].iloc[i]) if pd.notna(df['rsi'].iloc[i]) else None
        adx = int(df['adx'].iloc[i]) if pd.notna(df['adx'].iloc[i]) else None
        timestamp = format_timestamp(df['timestamp'].iloc[i])

        price_change = current_price - initial_price

        if 'SELL' == signal_type:
            if price_change < 0:
                character = '(+)'
            else:
                character = '(-)'
        else:
            if price_change < 0:
                character = '(-)'
            else:
                character = '(+)'

        price_percent_change = int((abs(price_change) / price_target) * 100)

        # log_line = f"Time {timestamp}, Price = {current_price} , RSI 1m = {rsi} , ADX 1m = {adx}, signal_type = {signal_type},  percent = {character}{price_percent_change}"
        # file.write(f"{log_line}\n")

        if price_percent_change >= 100 or price_change >= price_target:
            if character =='(+)':
                status = 'WIN'
                win += 1
            else:
                status = 'LOSS'
                loss += 1
            log_line = (f"Time {timestamp}, Price = {current_price} , RSI 1m = {rsi} , ADX 1m = {adx}\n"
                        f"===========> {status} ,percent {character} {price_percent_change}\n\n")
            file.write(log_line)

            return i, "Closed with 100% profit/loss"

    return len(df), "Signal still active"


def fetch_historical_data(symbol, interval, start_time, end_time):
    start_time_ts = str(pd.to_datetime(start_time).timestamp() * 1000)
    end_time_ts = str( pd.to_datetime(end_time).timestamp() * 1000)

    klines = client.futures_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=start_time_ts,
        end_str=end_time_ts
    )
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume',
                                       'close_time', 'quote_asset_volume', 'number_of_trades',
                                       'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df


def compare_time(time_str):

    time_obj = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S %Z')

    formatted_time_obj = time_obj.strftime('%Y%m%d%H%M%S')

    current_time = datetime.now(timezone.utc)
    formatted_current_time = current_time.strftime('%Y%m%d%H%M%S')

    if int(formatted_time_obj) > int(formatted_current_time):
        print(f"reset end time = time_current")
        return current_time.strftime('%Y-%m-%d %H:%M:%S %Z'), False
    return time_str, True



def fetch_multiple_days_data(symbol, interval, start_date, num_days):

    all_data = []
    current_time = datetime.now(timezone.utc)
    for day in range(num_days):
        start_time = (start_date + timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S UTC')
        end_time = (start_date + timedelta(days=day + 1)).strftime('%Y-%m-%d %H:%M:%S UTC')
        end_time_valid, is_continute = compare_time(end_time)

        df = fetch_historical_data(symbol, interval, start_time, end_time_valid)
        all_data.append(df)

        if is_continute is False:
            break
        if day%10 == 0:
            print(f"process to {day}")

    return pd.concat(all_data, ignore_index=True)


def calculate_indicators(df):
    df['rsi'] = ta.rsi(df['close'], length=14)
    # Tính ADX
    adx = ta.adx(df['high'], df['low'], df['close'], length=14)
    df['adx'] = adx['ADX_14']
    return df


def backtest_rsi_adx(start_date, day=1,interval='1m'):
    global price_target
    symbol = 'BTCUSDT'
    print(f"==>     start date {start_date}\n"
          f"==>     price target = {price_target}\n"
          f"==>     interval = {interval}\n")
    df = fetch_multiple_days_data(symbol, interval, start_date, day)
    df = calculate_indicators(df)
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{log_time()}.txt")
    pending_sell = False
    pending_buy = False

    global test_case, rsi_different
    print(f"tes_case = {test_case} rsi_different {rsi_different}")
    value = 25

    with open(log_file, 'w') as file:
        i = 0
        while i < len(df):
            rsi = int(df['rsi'].iloc[i]) if pd.notna(df['rsi'].iloc[i]) else None

            if i >= 10:
                recent_rsi = df['rsi'].iloc[i-10:i+1]
            else:
                recent_rsi = df['rsi'].iloc[:i+1]

            if len(recent_rsi) > 0:
                max_rsi = format_rsi(recent_rsi.max())
                min_rsi = format_rsi(recent_rsi.min())
            else:
                max_rsi = None
                min_rsi = None

            close_price = int(df['close'].iloc[i])
            timestamp = format_timestamp(df['timestamp'].iloc[i])

            """ đi tìm vị trí vào lệnh"""
            if rsi is None:
                i += 1
                # file.write(f"{log_line}\n")
                continue

            # if adx < 50:
            #     i += 1
            #     continue

            # if 25 < rsi < 75:
            #     i += 1
            #     continue


            if rsi >= (100-value):
                """sell"""
                if test_case == 1:
                    log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, signal_type = SELL"
                    file.write(f"{log_line}\n")
                    i, evaluation = evaluate_signal(df, i, "SELL", close_price, file)
                elif test_case == 2:
                    if max_rsi and rsi <= (max_rsi-rsi_different):
                        pending_sell = False
                        log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, pending_sell {pending_sell} signal_type = SELL"
                        file.write(f"{log_line}\n")
                        i, evaluation = evaluate_signal(df, i, "SELL", close_price, file)
                    else:
                        pending_sell = True
                        i += 1
                        log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi} , max = {max_rsi}, min  = {min_rsi} pending_sell {pending_sell}, WAITING"
                        file.write(f"{log_line}\n")

            elif rsi <= value:
                """ buy"""
                # case 1
                if test_case == 1:
                    log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, signal_type = BUY"
                    file.write(f"{log_line}\n")
                    i, evaluation = evaluate_signal(df, i, "BUY", close_price, file)
                elif test_case == 2:
                    """  """
                    if min_rsi and rsi >= (min_rsi+rsi_different):
                        pending_buy = False
                        log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, pending_buy {pending_buy} signal_type = BUY"
                        file.write(f"{log_line}\n")
                        i, evaluation = evaluate_signal(df, i, "BUY", close_price, file)
                    else:
                        pending_buy = True
                        i += 1
                        log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, pending_buy {pending_buy} WAITING"
                        file.write(f"{log_line}\n")

            elif pending_buy:
                pending_buy = False
                log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, signal_type = BUY"
                file.write(f"{log_line}\n")
                i, evaluation = evaluate_signal(df, i, "BUY", close_price, file)

            elif pending_sell:
                pending_sell = False
                log_line = f"time {timestamp}, Price = {close_price} , RSI 1m = {rsi}, max = {max_rsi}, min  = {min_rsi}, signal_type = SELL"
                file.write(f"{log_line}\n")
                i, evaluation = evaluate_signal(df, i, "SELL", close_price, file)
            else:
                i += 1



if __name__ == "__main__":
    date = '2024-11-06'
    day = 3
    interval = '5m'
    price_target = 600
    test_case = 1
    rsi_different = 3
    start_date = datetime.strptime(date, '%Y-%m-%d')
    # start_date = start_date.replace(hour=12, minute=30)
    print(f"\n************ BEGIN CHECK {start_date} + {day} day")
    backtest_rsi_adx(start_date, day,interval)

    print(f"\n************ FINAL TOTAL {win+loss},  WIN {win}, LOSS {loss}\n")





