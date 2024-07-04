import asyncio
import datetime
from telegram_utils.send_message import send

async def main(symbol='BTC/USDT', period=14, interval=60):
    while True:
        df_15m = fetch_ohlcv(symbol, '15m')
        df_15m = calculate_rsi(df_15m, period)
        current_rsi_15m = df_15m['rsi'].iloc[-1]

        message = f"RSI Alert! Current RSI for {symbol} on 15m timeframe is {current_rsi_15m:.2f}"
        print(message)
        if current_rsi_15m < 21:
            await send(message)
            await send(f"BUY {symbol} with price xxxx")
        if current_rsi_15m > 79:
            await send(message)
            await send(f"SELL {symbol} with price xxxx")
        time.sleep(interval)
if __name__ == "__main__":
    print(os.path.abspath(os.path.join(current_dir, 'common')))
    asyncio.run(main())
