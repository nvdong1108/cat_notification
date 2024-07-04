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

# Chạy ứng dụng Python của bạn
#CMD ["python", "app.py"]
CMD ["python", "./indicator/rsi_fetcher.py"]
