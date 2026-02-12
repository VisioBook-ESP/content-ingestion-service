.PHONY: help install install-dev clean test lint format run docker-build docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make clean          - Clean up cache and temporary files"
	@echo "  make test           - Run tests with coverage"
	@echo "  make lint           - Run linters (flake8, mypy)"
	@echo "  make format         - Format code (black, isort)"
	@echo "  make run            - Run the application locally"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker containers"
	@echo "  make docker-down    - Stop Docker containers"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov/ .mypy_cache/

test:
	pytest --cov=src --cov-report=term-missing --cov-report=html

lint:
	flake8 src tests --max-line-length=100 --extend-ignore=E203,W503
	mypy src --ignore-missing-imports

format:
	black src tests
	isort src tests

run:
	python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f app
