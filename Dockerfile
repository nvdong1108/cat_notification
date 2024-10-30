# Sử dụng một image Python chính thức từ Docker Hub
FROM python:3.12.4

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép file requirements.txt vào thư mục làm việc
COPY requirements.txt .

# Cài đặt các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép tất cả các file từ thư mục hiện tại vào thư mục làm việc trong container
COPY . .

# Sao chép file .env vào container
COPY .env .env

# Copy file `squeeze_pro.py` đã sửa vào đúng vị trí trong container
COPY ./lib/squeeze_pro.py /usr/local/lib/python3.12/site-packages/pandas_ta/momentum/squeeze_pro.py

# Chạy ứng dụng Python của bạn
#CMD ["python", "app.py"]
CMD ["python", "./indicator/rsi_fetcher.py"]
