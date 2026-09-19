.PHONY: install lint format test test-cov archi check-schema migration migrate seed catalog run

# Taken from the root .env when entering through `make -C server`: the
# instance's ports stay described in a single place.
-include ../.env

POSTGRES_PORT ?= 5432
API_PORT ?= 8000
# The test database follows the working one: same container, other schema.
TEST_DATABASE_URL ?= postgresql+asyncpg://timesheet:timesheet@localhost:$(POSTGRES_PORT)/timesheet_test

VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

install:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt

lint:
	$(VENV)/bin/isort --check-only src/ tests/
	$(PY) -m black --check src/ tests/
	$(VENV)/bin/ruff check src/ tests/
	$(PY) -m flake8 src/ tests/
	$(PY) -m mypy src/
	$(MAKE) archi

format:
	$(VENV)/bin/isort src/ tests/
	$(PY) -m black src/ tests/
	$(VENV)/bin/ruff check --fix src/ tests/

archi:
	$(VENV)/bin/lint-imports --config .importlinter

# Checks that the database the migrations describe is the one the models do.
# Needs an up-to-date database: run `make migrate` first.
check-schema:
	$(VENV)/bin/alembic check

test:
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) $(PY) -m pytest

test-cov:
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) $(PY) -m pytest --cov-report=html

migration:
	@read -p "Message de migration : " msg; \
	$(VENV)/bin/alembic revision --autogenerate -m "$$msg"

migrate:
	$(VENV)/bin/alembic upgrade head

seed:
	$(PY) -m scripts.seed

# Writes the service catalogue. `OUT` points it at the catalogue's repository:
# make catalog OUT=../../waat-tools/content/catalog.json
OUT ?= catalog.json
catalog:
	$(PY) -m scripts.export_catalog $(OUT)

run:
	$(VENV)/bin/uvicorn src.main:app --reload --port $(API_PORT)
