.PHONY: help install install-dev test lint format clean run-metrics-collector run-ingestion-api run-offline-trainer run-online-scorer run-action-engine run-dashboard

help:
	@echo "Available commands:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  test             Run tests with coverage"
	@echo "  lint             Run ruff linter"
	@echo "  format           Format code with ruff"
	@echo "  clean            Remove build artifacts and cache"
	@echo "  run-metrics-collector    Run metrics collector service"
	@echo "  run-ingestion-api        Run ingestion API service"
	@echo "  run-offline-trainer      Run offline trainer service"
	@echo "  run-online-scorer        Run online scorer service"
	@echo "  run-action-engine        Run action engine service"
	@echo "  run-dashboard            Run dashboard service"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest --cov --cov-report=term-missing --cov-report=html

lint:
	ruff check .

format:
	ruff format .
	ruff check . --fix

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build dist htmlcov .coverage coverage.xml

run-metrics-collector:
	python services/metrics-collector/main.py

run-ingestion-api:
	uvicorn services.ingestion-api.main:app --host 0.0.0.0 --port 8000 --reload

run-offline-trainer:
	python services/anomaly-engine/offline-trainer/main.py

run-online-scorer:
	python services/anomaly-engine/online-scorer/main.py

run-action-engine:
	python services/action-engine/main.py

run-dashboard:
	python services/dashboard/main.py
