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

res:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) up --build -d
	$(DOCKER_COMPOSE) logs -f

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

PYTHON_RUN = $(DOCKER_COMPOSE) exec -T admin_panel python

.PHONY: test-flows test-gen-list test-gen-random test-gen-exact test-gen-clean test-scenario-overflow test-scenario-all

test-flows:
	@echo "📋 Available flows:"
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --list

test-gen-list: test-flows

test-gen-random:
	@echo "🎲 Creating random number of posts for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id $(FLOW_ID)

test-gen-exact:
	@echo "🎯 Creating $(COUNT) posts for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id $(FLOW_ID) --exact $(COUNT)

test-gen-range:
	@echo "🎲 Creating random posts ($(MIN)-$(MAX)) for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id $(FLOW_ID) --min-posts $(MIN) --max-posts $(MAX)

test-gen-clean:
	@echo "🧹 Cleaning test posts for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id $(FLOW_ID) --delete

test-scenario-overflow:
	@echo "🧪 Running overflow scenario for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id $(FLOW_ID) --scenario overflow

test-scenario-publish:
	@echo "🧪 Running publish cycle scenario for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id $(FLOW_ID) --scenario publish-cycle

test-scenario-schedule:
	@echo "🧪 Running schedule scenario for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id $(FLOW_ID) --scenario schedule

test-scenario-edge:
	@echo "🧪 Running edge cases scenario for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id $(FLOW_ID) --scenario edge-cases

test-scenario-all:
	@echo "🧪 Running ALL scenarios for flow $(FLOW_ID)..."
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id $(FLOW_ID) --scenario all

test-quick:
	@echo "⚡ Quick test: 10 posts for flow 1"
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id 1 --exact 10

test-overflow:
	@echo "🌊 Overflow test: 50 posts for flow 1"
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id 1 --exact 50

test-full:
	@echo "🎯 Full test suite for flow 1"
	@$(PYTHON_RUN) /app/scripts/test_flow_scenarios.py --flow-id 1 --scenario all

test-clean-all:
	@echo "🧹 Cleaning all test posts for flow 1"
	@$(PYTHON_RUN) /app/scripts/test_post_generation.py --flow-id 1 --delete

# Help for test commands
test-help:
	@echo "╔════════════════════════════════════════════════════════════════╗"
	@echo "║         📚 TeleGen Post Generation Test Commands              ║"
	@echo "╚════════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "⚠️  SYNTAX: make command FLOW_ID=N (NOT --flow-id)"
	@echo ""
	@echo "📋 List & Info:"
	@echo "  make test-flows              List all available flows"
	@echo ""
	@echo "🎲 Generate Posts:"
	@echo "  make test-gen-random FLOW_ID=2          Random 5-15 posts"
	@echo "  make test-gen-exact FLOW_ID=2 COUNT=10  Exact number"
	@echo "  make test-gen-range FLOW_ID=2 MIN=3 MAX=8  Custom range"
	@echo ""
	@echo "🧪 Test Scenarios:"
	@echo "  make test-scenario-overflow FLOW_ID=2   Test overflow (2x posts)"
	@echo "  make test-scenario-publish FLOW_ID=2    Test publish cycle"
	@echo "  make test-scenario-schedule FLOW_ID=2   Test scheduling"
	@echo "  make test-scenario-edge FLOW_ID=2       Test edge cases"
	@echo "  make test-scenario-all FLOW_ID=2        Run ALL scenarios"
	@echo ""
	@echo "⚡ Quick Shortcuts (for flow 1):"
	@echo "  make test-quick              Create 10 posts"
	@echo "  make test-overflow           Create 50 posts"
	@echo "  make test-full               Run full test suite"
	@echo ""
	@echo "🧹 Cleanup:"
	@echo "  make test-gen-clean FLOW_ID=2            Clean specific flow"
	@echo "  make test-clean-all                      Clean flow 1"
	@echo ""
	@echo "💡 Examples:"
	@echo "  make test-flows"
	@echo "  make test-gen-exact FLOW_ID=2 COUNT=20"
	@echo "  make test-scenario-publish FLOW_ID=2"
	@echo "  make test-quick && make test-clean-all"
	@echo ""
	@echo "🔍 Note: Commands run inside Docker containers"
	@echo ""
