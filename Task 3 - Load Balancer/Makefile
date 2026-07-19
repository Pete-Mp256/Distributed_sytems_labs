SERVER_IMAGE=ds-server:latest
LB_IMAGE=ds-loadbalancer:latest

.PHONY: build up down logs clean restart

build:
	docker build -t $(SERVER_IMAGE) ./server
	docker build -t $(LB_IMAGE) ./load_balancer

up: build
	docker-compose up -d

down:
	docker-compose down
	-docker rm -f $$(docker ps -aq --filter network=net1) 2>/dev/null

restart: down up

logs:
	docker-compose logs -f loadbalancer

clean: down
	-docker rmi $(SERVER_IMAGE) $(LB_IMAGE) 2>/dev/null
