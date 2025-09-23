DOCKER_COMPOSE = docker-compose
MANAGE = docker-compose exec admin_panel python /app/manage.py

.PHONY: up down build restart logs clean migrate superuser test

up:
	$(DOCKER_COMPOSE) up --build -d

run:
	$(DOCKER_COMPOSE) up

build:
	$(DOCKER_COMPOSE) build

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up

rebuild:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up --build

logs:
	$(DOCKER_COMPOSE) logs -f

clean:
	$(DOCKER_COMPOSE) down -v --remove-orphans

migrate:
	$(MANAGE) makemigrations
	$(MANAGE) migrate

createsuperuser:
	$(MANAGE) createsuperuser

collectstatic:
	$(MANAGE) collectstatic --noinput

create-test-data:
	$(MANAGE) generate_test_data --users 3

clean-test-data:
	$(MANAGE) cleanup_test_data

seed:
	$(MANAGE) seed_data

shell:
	$(MANAGE) shell

bash:
	docker-compose exec admin_panel bash

db-shell:
	docker-compose exec db psql -U $(DB_USER) -d $(DB_NAME)

status:
	$(DOCKER_COMPOSE) ps

admin:
	open http://localhost:8000/admin

test:
	docker-compose run --rm tests
