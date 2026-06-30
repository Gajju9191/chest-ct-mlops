
.PHONY: help setup install test lint format clean docker-build docker-up deploy

help:
	@echo "Available commands:"
	@echo "  setup          Setup the project"
	@echo "  install        Install dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linters"
	@echo "  format        Format code"
	@echo "  clean         Clean temporary files"
	@echo "  docker-build  Build Docker images"
	@echo "  docker-up     Start Docker services"
	@echo "  deploy        Deploy to ECS"

setup:
	@echo "Setting up project..."
	python -m pip install --upgrade pip
	pip install -r requirements.txt
	pip install -e .
	dvc init
	cp .env.example .env

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/ -v --cov=src --cov-report=html

lint:
	flake8 src/ tests/
	mypy src/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/
	rm -rf build/ dist/

docker-build:
	docker build -f docker/Dockerfile.prod -t chest-ct-api .

docker-up:
	docker-compose -f docker-compose.yml up -d

deploy:
	@echo "Deploying to ECS..."
	cd terraform && terraform apply -auto-approve