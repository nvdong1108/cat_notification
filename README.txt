# build Docker image 
docker build -t cat-notification .

# run docker
docker run -d --name  cat-notification-container cat-notification
docker run -d --name cat-notification -v C:\SourceCode\DongNV\Git\BotTradingBinace\Docker_logs:/logs cat-notification

#đi đên thư mục Source 
docker exec -it cat-notification sh
# xem log 
tail -f log-rsi-20240702.log

# xem danh sách image 
docker image

# Đổi tên image : 
docker tag cat-notification:latest nvdong1108/cat-notification:latest
#Đẩy image lên Docker Hub:
docker push nvdong1108/cat-notification:latest

# pull image về 
docker pull nvdong1108/cat-notification:latest
# run docker 
docker run -d --name my-container nvdong1108/cat-notification:latest

