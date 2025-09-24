DOCKER_COMPOSE = docker-compose -f deployments/docker-compose.yml --env-file .env
MANAGE = $(DOCKER_COMPOSE) exec admin_panel python manage.py

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
	$(DOCKER_COMPOSE) restart

rebuild:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up --build -d

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
	$(DOCKER_COMPOSE) exec admin_panel bash

db-shell:
	$(DOCKER_COMPOSE) exec db psql -U $(DB_USER) -d $(DB_NAME)

status:
	$(DOCKER_COMPOSE) ps

admin:
	open http://localhost:8000/admin

test:
	$(DOCKER_COMPOSE) run --rm admin_panel python -m pytest

bot-logs:
	$(DOCKER_COMPOSE) logs -f bot

celery-logs:
	$(DOCKER_COMPOSE) logs -f celery_worker

# Дополнительные полезные команды
backup-db:
	$(DOCKER_COMPOSE) exec db pg_dump -U $(DB_USER) $(DB_NAME) > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@echo "Usage: cat backup_file.sql | $(DOCKER_COMPOSE) exec -T db psql -U $(DB_USER) $(DB_NAME)"

redis-cli:
	$(DOCKER_COMPOSE) exec redis redis-cli

# Для разработки
dev:
	$(DOCKER_COMPOSE) -f deployments/docker-compose.yml -f deployments/docker-compose.dev.yml up

stop:
	$(DOCKER_COMPOSE) stop
