# PonyAgent Makefile
# Usage: make <target>

.PHONY: help install dev test lint coverage format build clean docker push docker-run

PYTHON ?= python3
VENV ?= .venv
PIP ?= pip

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && $(PIP) install -e ".[dev]"

dev: ## Install in development mode
	$(PYTHON) -m pip install -e ".[dev]"

test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ --cov=ponyagent --cov-report=html --cov-report=term-missing

test-fast: ## Run tests (quiet)
	$(PYTHON) -m pytest tests/ -q

lint: ## Run linter
	$(PYTHON) -m ruff check ponyagent/ tests/

lint-fix: ## Auto-fix lint issues
	$(PYTHON) -m ruff check ponyagent/ tests/ --fix

format: ## Format code
	$(PYTHON) -m ruff format ponyagent/ tests/

typecheck: ## Run type checker
	$(PYTHON) -m mypy ponyagent/ --ignore-missing-imports 2>/dev/null || echo "mypy not installed"

build: lint test ## Lint + test before build
	$(PYTHON) -m build 2>/dev/null || echo "build not installed, skipping"

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache htmlcov/

docker: ## Build Docker image
	docker build -t ponyagent:latest .

docker-run: ## Run PonyAgent container
	docker run --rm -p 8000:8000 ponyagent:latest

push: docker ## Push Docker image
	docker push ponyagent:latest
