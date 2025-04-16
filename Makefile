DOCKER_COMPOSE = docker-compose
MANAGE = docker-compose exec admin_panel python manage.py

.PHONY: up down build restart logs clean migrate superuser test

up:
	$(DOCKER_COMPOSE) up --build -d

run:
	$(DOCKER_COMPOSE) up -d --no-build

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

superuser:
	$(MANAGE) createsuperuser

test:
	$(MANAGE) test

seed:
	$(MANAGE) seed_data
shell:
	$(MANAGE) shell

db-shell:
	docker-compose exec db psql -U $(DB_USER) -d $(DB_NAME)

status:
	$(DOCKER_COMPOSE) ps

admin:
	open http://localhost:8000/admin