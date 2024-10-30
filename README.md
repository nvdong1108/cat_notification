# Step 1.  import project
pip instell -r .\requirements.txt

 

# build Docker image 
docker build -t cat-notification .

# run docker
docker run -d --name cat-bot-1 cat-notification



docker run -d --name cat-notification -v C:\SourceCode\DongNV\Git:/logs cat-notification

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

# xem log 

docker logs cat-bot-1


docker exec -it <container_id_or_name> date




docker run -d --name cat1  -v C:\SourceCode\DongNV\Git\Bot_cat\logs:/logs cat1

/etc/localtime:/etc/localtime:ro -d 

docker run -e TZ=Asia/Ho_Chi_Minh -d cat1



