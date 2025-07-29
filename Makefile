.PHONY: help run dev test test-watch lint format type-check build install clean db-init db-migrate db-backup release package

# Default target
help:
	@echo "PromptRiff Development Commands"
	@echo "==============================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make run          - Run PromptRiff from source"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Run development server with hot reload"
	@echo "  make test         - Run all tests"
	@echo "  make test-watch   - Run tests in watch mode"
	@echo "  make lint         - Run all linters (ruff, mypy)"
	@echo "  make format       - Format code with black/ruff"
	@echo "  make type-check   - Run mypy type checking"
	@echo ""
	@echo "Build:"
	@echo "  make build        - Build application"
	@echo "  make install      - Install dependencies with uv"
	@echo "  make clean        - Clean build artifacts"
	@echo ""
	@echo "Database:"
	@echo "  make db-init      - Initialize database"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-backup    - Backup database"
	@echo ""
	@echo "Release:"
	@echo "  make release      - Build release version"
	@echo "  make package      - Create distributable package"

# Development targets
dev:
	@echo "Starting development server..."
	uv run python -m promptriff --dev

run:
	@echo "Starting PromptRiff..."
	uv run python -m promptriff

test:
	@echo "Running tests..."
	uv run pytest

test-watch:
	@echo "Running tests in watch mode..."
	uv run pytest-watch

lint:
	@echo "Running linters..."
	uv run ruff check .
	uv run mypy src/

format:
	@echo "Formatting code..."
	uv run black .
	uv run ruff check --fix .

type-check:
	@echo "Running type checking..."
	uv run mypy src/

# Build targets
build: clean
	@echo "Building application..."
	uv build

install:
	@echo "Installing dependencies..."
	uv sync --all-extras

install-dev: install
	@echo "Installing pre-commit hooks..."
	uv run pre-commit install

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Database targets
db-init:
	@echo "Initializing database..."
	uv run python -m promptriff.database.init

db-migrate:
	@echo "Running database migrations..."
	uv run python -m promptriff.database.migrate

db-backup:
	@echo "Backing up database..."
	@mkdir -p backups
	@cp ~/.local/share/promptriff/promptriff.db backups/promptriff_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to backups/"

# Release targets
release: clean lint type-check test build
	@echo "Release build complete!"

package: release
	@echo "Creating distributable package..."
	uv build --wheel

# Additional development helpers
.PHONY: setup
setup: install-dev db-init
	@echo "Development environment setup complete!"
	@echo "Run 'make dev' to start the development server"

.PHONY: check
check: lint type-check test
	@echo "All checks passed!"

.PHONY: update
update:
	@echo "Updating dependencies..."
	uv sync --upgrade

.PHONY: tree
tree:
	@tree -I '__pycache__|*.pyc|.git|.mypy_cache|.ruff_cache|.pytest_cache|htmlcov|build|dist|*.egg-info' .