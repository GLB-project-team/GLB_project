IMAGE_NAME				= my-flask-app
DOCKER_COMPOSE_YAML		= docker-compose.yaml
DOCKER_DATA_DIR			= ./chromaDB

build: $(DOCKER_DATA_DIR)
	docker-compose -f $(DOCKER_COMPOSE_YAML) build --no-cache

up:
	docker-compose -f $(DOCKER_COMPOSE_YAML) up -d

$(DOCKER_DATA_DIR) :
	powershell -Command "New-Item -Path '$(DOCKER_DATA_DIR)' -ItemType Directory -Force"

down:
	docker-compose -f $(DOCKER_COMPOSE_YAML) down

re: down build

ps:
	docker ps -a

clean:
	docker-compose -f $(DOCKER_COMPOSE_YAML) down --volumes
	docker system prune -a
	docker image prune -a

fclean:
	docker-compose -f $(DOCKER_COMPOSE_YAML) down --volumes
	docker system prune -a
	rm -rf ./chromaDB

Acsa:
	docker exec -it back_api-app-1 /bin/sh

Acsc:
	docker exec -it back_api-worker-1 /bin/sh

loga:
	docker logs back_api-app-1

logc:
	docker logs back_api-worker-1

logs:
	docker logs back_api-app-1
	docker logs back_api-worker-1

buildx:
	docker buildx build --platform linux/amd64 --tag $(IMAGE_NAME) ./server/

.PHONY: build up down re ps clean fclean Acsa Acsc loga logc logs buildx