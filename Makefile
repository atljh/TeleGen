DOCKER_COMPOSE = docker-compose -f deployments/docker-compose.yml --env-file .env
TEST_DOCKER_COMPOSE = docker-compose -f deployments/docker-compose.test.yml --env-file .env.test

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

makemigrations:
	$(MANAGE) makemigrations

migrate:
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
	$(DOCKER_COMPOSE) exec db psql -U telegen_user -d telegen_db

status:
	$(DOCKER_COMPOSE) ps

admin:
	open http://localhost:8000/admin

bot-logs:
	$(DOCKER_COMPOSE) logs -f bot

celery-logs:
	$(DOCKER_COMPOSE) logs -f celery_worker

backup-db:
	$(DOCKER_COMPOSE) exec db pg_dump -U $(DB_USER) $(DB_NAME) > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db:
	@echo "Usage: cat backup_file.sql | $(DOCKER_COMPOSE) exec -T db psql -U $(DB_USER) $(DB_NAME)"

redis-cli:
	$(DOCKER_COMPOSE) exec redis redis-cli

dev:
	$(DOCKER_COMPOSE) -f deployments/docker-compose.yml -f deployments/docker-compose.dev.yml up

stop:
	$(DOCKER_COMPOSE) stop


test:
	${TEST_DOCKER_COMPOSE} up --build --abort-on-container-exit tests

test-unit:
	${TEST_DOCKER_COMPOSE} run tests python -m pytest tests/unit/ -v

test-integration:
	${TEST_DOCKER_COMPOSE} run tests python -m pytest tests/integration/ -v

test-e2e:
	${TEST_DOCKER_COMPOSE} run tests python -m pytest tests/e2e/ -v

test-coverage:
	${TEST_DOCKER_COMPOSE} run tests python -m pytest --cov=bot --cov=admin_panel --cov-report=html:htmlcov

lint:
	${TEST_DOCKER_COMPOSE} up linter

test-all: lint test

test-local:
	export DJANGO_SETTINGS_MODULE=core.settings.testing && \
	pytest -v --disable-warnings --cov=bot --cov=admin_panel

clean-test:
	docker-compose -f docker-compose.test.yml down -v
	rm -rf htmlcov .coverage

test-debug:
	docker-compose -f deployments/docker-compose.test.yml run tests bash -c "pwd && ls -la && python -c 'import sys; print(sys.path)'"
