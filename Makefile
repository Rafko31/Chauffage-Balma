.PHONY: setup up down migrate seed test-unit test-integration demo clean

ARTIFACTS_DIR ?= ./artifacts
DATABASE_URL ?= sqlite:///./test.db

setup:
	pip install -r requirements.txt
	playwright install --with-deps chromium

up:
	docker-compose up -d

down:
	docker-compose down

migrate:
	alembic upgrade head

seed:
	python -m src.pulse_ia.scripts.seed_demo

test-unit:
	DATABASE_URL=sqlite:///./test_unit.db python -m pytest src/pulse_ia/tests/test_survey.py src/pulse_ia/tests/test_analytics.py

test-integration:
	@echo "Starting test database..."
	docker run --name pulse_ia_test_db -e POSTGRES_PASSWORD=postgres -p 5433:5432 -d postgres:15
	@sleep 5
	@echo "Running migrations..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres alembic upgrade head
	@echo "Checking schema alignment..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres alembic check
	@echo "Running tests..."
	DATABASE_URL=postgresql://postgres:postgres@localhost:5433/postgres python -m pytest src/pulse_ia/tests/
	@echo "Cleaning up..."
	docker stop pulse_ia_test_db && docker rm pulse_ia_test_db

demo: clean
	@if [ ! -f .env ]; then cp .env.example .env; fi
	docker-compose up --build

clean:
	docker-compose down -v --remove-orphans
	rm -f *.db temp.db test_unit.db test_integration.db
	rm -rf artifacts/*.pdf
	find . -type d -name "__pycache__" -exec rm -rf {} +
