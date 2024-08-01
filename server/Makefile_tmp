# Makefile

# 변수 설정
IMAGE_NAME = my-flask-app
CONTAINER_NAME = flask-container
# PATH 자신의 경로대로 바꿀 것!
PROJECT_PATH=C:/Users/zero/GLB-project
HOST_PORT = 5000
CONTAINER_PORT = 5000
DOCKER_DATA_DIR	= ./vectorDB

# Docker 이미지 빌드
build: $(DOCKER_DATA_DIR)
	docker build -t $(IMAGE_NAME) .

$(DOCKER_DATA_DIR):
	powershell -Command "New-Item -Path '$(DOCKER_DATA_DIR)/book_content' -ItemType Directory -Force"

# Docker 컨테이너 실행 (볼륨 마운트 포함)
run:
	docker run --rm -d --name $(CONTAINER_NAME) -p $(HOST_PORT):$(CONTAINER_PORT) -v ${PWD}:/app -e FLASK_ENV=development $(IMAGE_NAME)

powerun:
	docker run --rm -d --name $(CONTAINER_NAME) -p $(HOST_PORT):$(CONTAINER_PORT) -v ${PROJECT_PATH}:/app -e FLASK_ENV=development $(IMAGE_NAME)

rrun:
	docker run -d -p $(HOST_PORT):$(CONTAINER_PORT)/tcp --name $(CONTAINER_NAME) $(IMAGE_NAME)
# -v ${PROJECT_PATH}:/app

# 로그 보기
logs:
	docker logs -f $(CONTAINER_NAME)

# 컨테이너 중지
stop:
	docker stop $(CONTAINER_NAME)

ps:
	docker ps -a

acs:
	docker exec -it $(CONTAINER_NAME) /bin/sh

# 컨테이너 재시작
restart: stop run

# 컨테이너 및 이미지 삭제 (clean)
clean:
	-docker stop $(CONTAINER_NAME)
	-docker rm $(CONTAINER_NAME)
	-docker rmi $(IMAGE_NAME)

# 모든 Docker 리소스 정리 (fclean)
fclean: clean
	-docker system prune -af

# 도움말
help:
	@echo "Available commands:"
	@echo "  make build    : Build Docker image"
	@echo "  make run      : Run Docker container with volume mount"
	@echo "  make logs     : View container logs"
	@echo "  make stop     : Stop running container"
	@echo "  make restart  : Restart the container"
	@echo "  make clean    : Remove container and image"
	@echo "  make fclean   : Remove all Docker resources"

.PHONY: build run logs stop restart clean fclean help acs mk