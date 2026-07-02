setup:
	pip install -r requirements.txt
	playwright install --with-deps chromium

migrate:
	export DATABASE_URL=$(DATABASE_URL) && alembic upgrade head

seed:
	python -m src.pulse_ia.scripts.seed_demo

test:
	python -m pytest src/pulse_ia/tests/

demo: setup migrate seed
	uvicorn src.pulse_ia.main:app --reload
