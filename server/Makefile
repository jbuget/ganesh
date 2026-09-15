.PHONY: install lint format test test-cov archi migration migrate seed run

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

test:
	$(PY) -m pytest

test-cov:
	$(PY) -m pytest --cov-report=html

migration:
	@read -p "Message de migration : " msg; \
	$(VENV)/bin/alembic revision --autogenerate -m "$$msg"

migrate:
	$(VENV)/bin/alembic upgrade head

seed:
	$(PY) -m scripts.seed

run:
	$(VENV)/bin/uvicorn src.main:app --reload --port $${API_PORT:-8004}
