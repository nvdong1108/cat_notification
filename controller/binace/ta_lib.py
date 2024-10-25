import talib
import pandas as pd

# Ví dụ dữ liệu giá (OHLCV)
data = pd.DataFrame({
    'open': [100, 102, 101, 105, 108],
    'high': [105, 106, 104, 110, 115],
    'low': [99, 100, 100, 103, 107],
    'close': [104, 101, 102, 109, 110],
    'volume': [1500, 1200, 1300, 1100, 1600]
})

# Phát hiện mô hình Bullish Engulfing
engulfing = talib.CDLENGULFING(data['open'], data['high'], data['low'], data['close'])

# In kết quả
print(engulfing)

# Kết quả sẽ trả về mảng với giá trị 100 nếu có mô hình Bullish Engulfing,
# -100 nếu có mô hình Bearish Engulfing, và 0 nếu không có mô hình.
