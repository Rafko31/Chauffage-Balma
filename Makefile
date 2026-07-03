.PHONY: setup up down migrate seed test-unit test-integration demo clean

SHELL := /bin/bash

setup:
	@echo "Local setup (requires Python 3.12)"
	pip install -r requirements.txt
	playwright install --with-deps chromium

up:
	@if [ ! -f .env ]; then cp .env.example .env; fi
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose run --rm api alembic upgrade head

seed:
	docker compose run --rm api python -m src.pulse_ia.scripts.seed_demo

test-unit:
	@echo "Running unit tests (SQLite)..."
	DATABASE_URL=sqlite:///./test_unit.db python -m pytest src/pulse_ia/tests/test_survey.py src/pulse_ia/tests/test_analytics.py
	@rm -f test_unit.db

test-integration: clean
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@echo "Starting ephemeral infrastructure for integration tests..."
	docker compose up -d db
	@echo "Waiting for PostgreSQL to be ready..."
	@until docker compose exec db pg_isready -U postgres; do sleep 1; done
	@echo "Running migrations and tests inside the API container..."
	docker compose run --rm \
		-e DATABASE_URL=postgresql://postgres:postgres@db:5432/pulse_ia \
		api \
		sh -c "alembic upgrade head && alembic check && pytest src/pulse_ia/tests/"
	@echo "Cleaning up..."
	docker compose down -v --remove-orphans

demo: clean
	@if [ ! -f .env ]; then cp .env.example .env; fi
	docker compose up -d db
	@echo "Waiting for database..."
	@until docker compose exec db pg_isready -U postgres; do sleep 1; done
	@echo "Running migrations..."
	docker compose run --rm api alembic upgrade head
	@echo "Running seed..."
	docker compose run --rm api python -m src.pulse_ia.scripts.seed_demo
	@echo "Starting API..."
	docker compose up -d api
	@echo "Waiting for API to be ready..."
	@until curl -s -f http://localhost:8000/ready > /dev/null; do sleep 1; done
	@echo "Checking artifacts..."
	@if [ -f artifacts/manufacture_innovante_direction_q1.pdf ] && [ -f artifacts/manufacture_innovante_ca_q1.pdf ]; then \
		echo "Success: Reports generated in ./artifacts/"; \
	else \
		echo "Error: Reports not found!"; exit 1; \
	fi
	@echo "Demo is running at http://localhost:8000"

clean:
	docker compose down -v --remove-orphans
	rm -f *.db temp.db test_unit.db test_integration.db
	rm -rf artifacts/*.pdf
	find . -type d -name "__pycache__" -exec rm -rf {} +
