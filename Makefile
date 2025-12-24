.PHONY: help install test lint format clean run docs

help:
	@echo "Syndicate Argmax Prediction System - Make Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make test-unit  - Run unit tests only"
	@echo "  make test-int   - Run integration tests only"
	@echo "  make lint       - Run code linting"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Clean temporary files"
	@echo "  make run        - Run the system"
	@echo "  make docs       - Generate documentation"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v -m unit

test-integration:
	pytest tests/integration/ -v -m integration

test-system:
	pytest tests/system/ -v -m system

lint:
	flake8 src/ tests/
	mypy src/

format:
	black src/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ htmlcov/ .coverage .pytest_cache/

run:
	python -m src.web_ui.app

setup:
	mkdir -p data/cache data/historical data/models logs
	cp .env.example .env 2>/dev/null || true
	@echo "Setup complete. Please edit .env with your configuration."

docs:
	@echo "Documentation generation not yet implemented"
