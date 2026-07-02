.PHONY: setup up down migrate seed test-unit test-integration demo clean

SHELL := /bin/bash

# Configuration
ENV_FILE ?= .env
include $(ENV_FILE)
export $(shell sed 's/=.*//' $(ENV_FILE))

setup:
	@echo "Local setup (requires Python 3.12)"
	pip install -r requirements.txt
	playwright install --with-deps chromium

up:
	docker compose up -d

down:
	docker compose down

migrate:
	docker compose exec api alembic upgrade head

seed:
	docker compose exec api python -m src.pulse_ia.scripts.seed_demo

test-unit:
	@echo "Running unit tests (SQLite)..."
	DATABASE_URL=sqlite:///./test_unit.db python -m pytest src/pulse_ia/tests/test_survey.py src/pulse_ia/tests/test_analytics.py
	@rm -f test_unit.db

test-integration: clean-test-db
	@echo "Starting ephemeral PostgreSQL for integration tests..."
	docker run --name pulse_ia_test_pg -e POSTGRES_PASSWORD=postgres -p 5433:5432 -d postgres:15
	@echo "Waiting for PostgreSQL to be ready..."
	@until docker exec pulse_ia_test_pg pg_isready -U postgres; do sleep 1; done
	@echo "Running migrations against PostgreSQL..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres alembic upgrade head
	@echo "Checking schema alignment..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres alembic check
	@echo "Running integration tests..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres python -m pytest src/pulse_ia/tests/
	@echo "Cleaning up PostgreSQL..."
	@docker stop pulse_ia_test_pg && docker rm pulse_ia_test_pg

demo: clean
	@if [ ! -f .env ]; then cp .env.example .env; fi
	docker compose up -d --build
	@echo "Waiting for API to be ready..."
	@until curl -s -f http://localhost:8000/ready > /dev/null; do sleep 1; done
	@echo "API is ready. Generating demonstration reports..."
	docker compose exec api python -m src.pulse_ia.scripts.seed_demo
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

clean-test-db:
	@docker stop pulse_ia_test_pg >/dev/null 2>&1 || true
	@docker rm pulse_ia_test_pg >/dev/null 2>&1 || true
