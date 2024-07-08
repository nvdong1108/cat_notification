import ccxt
import pandas as pd
import numpy  as np
from datetime import datetime, timedelta


def fetch_historical_data(symbol, timeframe, since, limit):
    binance = ccxt.binance()
    ohlcv = binance.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

def backtest(symbol, timeframe, start_date, end_date):
    binance = ccxt.binance()
    initial_balance = 1000  # Số tiền ban đầu
    balance = initial_balance
    btc = 0
    btc_per_trade = 0.002
    leverage = 5
    current_date = start_date

    while current_date <= end_date:
        since = int(current_date.timestamp() * 1000)
        limit = 1000  
        df = fetch_historical_data(symbol, timeframe, since, limit)

        df = calculate_rsi(df)
        apply_strategy(df)

        # Chạy backtest cho dữ liệu lần này
        for i in range(len(df)):
            if df['position'][i] == 1 and balance >= (btc_per_trade * df['close'][i] / leverage):
                # Mua BTC với đòn bẩy
                investment = btc_per_trade * df['close'][i] / leverage
                btc += btc_per_trade
                balance -= investment
                cost_per_trade =  btc_per_trade * df['close'][i] / leverage
                print(f"Bought {btc_per_trade} BTC at price {df['close'][i]}. Cost: {cost_per_trade}. Leverage: {leverage}x.")
                if (df['close'][i] - df['close'][i-1]) * btc > cost_per_trade:
                    balance += (df['close'][i] - df['close'][i-1]) * btc
                    btc = 0
                    print(f"Profit: {(df['close'][i] - df['close'][i-1]) * btc}")
                    break
                elif (df['close'][i] - df['close'][i-1]) * btc < - cost_per_trade:
                    balance -= (df['close'][i] - df['close'][i-1]) * btc
                    btc = 0
                    print(f"Loss: {(df['close'][i] - df['close'][i-1]) * btc}")
                    break
            elif df['position'][i] == -1 and btc >= btc_per_trade:
                # Bán BTC
                balance += btc_per_trade * df['close'][i]
                btc -= btc_per_trade
                cost_per_trade =  btc_per_trade * df['close'][i] / leverage

                print(f"Sold {btc_per_trade} BTC at price {df['close'][i]}. Revenue: {btc_per_trade * df['close'][i]}. Leverage: {leverage}x.")
                if (df['close'][i] - df['close'][i-1]) * btc > cost_per_trade:
                    balance += (df['close'][i] - df['close'][i-1]) * btc
                    btc = 0
                    print(f"Profit: {(df['close'][i] - df['close'][i-1]) * btc}")
                    break
                elif (df['close'][i] - df['close'][i-1]) * btc < - cost_per_trade:
                    balance -= (df['close'][i] - df['close'][i-1]) * btc
                    btc = 0
                    print(f"Loss: {(df['close'][i] - df['close'][i-1]) * btc}")
                    break

        # Cập nhật lại thời điểm bắt đầu cho lần fetch tiếp theo
        current_date += timedelta(days=1)  # Cập nhật current_date theo ý muốn (vd: 1 ngày)

    final_balance = balance + (btc * df['close'].iloc[-1])  # Tính toán số dư cuối cùng
    return final_balance

# Hàm tính toán RSI
def calculate_rsi(df, period=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# Hàm áp dụng chiến lược giao dịch
def apply_strategy(df):
    df['signal'] = 0
    df['signal'] = np.where(df['RSI'] > 75, -1, np.where(df['RSI'] < 25, 1, 0))
    df['position'] = df['signal'].diff()

# Thực hiện backtest cho BTC/USDT với khung thời gian 15 phút
symbol = 'BTC/USDT'
timeframe = '15m'
start_date = datetime(2024, 6, 20)  # Ngày bắt đầu backtest (vd: 1/4/2023)
end_date = datetime(2024,6,30) # Ngày kết thúc backtest (vd: ngày hiện tại)


final_balance = backtest(symbol, timeframe, start_date, end_date)
print(f"Final balance: ${final_balance:.2f}")
