.PHONY: help dev test test-watch lint format type-check build install clean db-init db-migrate db-backup release package all check

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python
UV := uv
PROJECT_NAME := promptriff
SRC_DIR := src
TEST_DIR := tests
DB_PATH := ~/.local/share/promptriff/promptriff.db
CONFIG_PATH := ~/.config/promptriff

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo '${BLUE}PromptRiff Development Commands${NC}'
	@echo ''
	@echo 'Usage:'
	@echo '  ${YELLOW}make${NC} ${GREEN}<target>${NC}'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  ${YELLOW}%-15s${NC} %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development
dev: install ## Run development server with hot reload
	@echo "${BLUE}Starting development server...${NC}"
	$(UV) run -- $(PYTHON) -m promptriff.main --dev

test: ## Run all tests
	@echo "${BLUE}Running tests...${NC}"
	$(UV) run pytest -v

test-watch: ## Run tests in watch mode
	@echo "${BLUE}Running tests in watch mode...${NC}"
	$(UV) run pytest-watch

lint: ## Run all linters (ruff, mypy)
	@echo "${BLUE}Running linters...${NC}"
	@echo "${YELLOW}Running ruff...${NC}"
	$(UV) run ruff check $(SRC_DIR) $(TEST_DIR)
	@echo "${YELLOW}Running mypy...${NC}"
	$(UV) run mypy $(SRC_DIR)

format: ## Format code with black/ruff
	@echo "${BLUE}Formatting code...${NC}"
	$(UV) run black $(SRC_DIR) $(TEST_DIR)
	$(UV) run ruff check --fix $(SRC_DIR) $(TEST_DIR)

type-check: ## Run mypy type checking
	@echo "${BLUE}Running type checking...${NC}"
	$(UV) run mypy $(SRC_DIR)

check: lint type-check test ## Run all checks (lint, type-check, test)

# Build
build: clean ## Build application
	@echo "${BLUE}Building application...${NC}"
	$(UV) build

install: ## Install dependencies with uv
	@echo "${BLUE}Installing dependencies...${NC}"
	$(UV) sync

clean: ## Clean build artifacts
	@echo "${BLUE}Cleaning build artifacts...${NC}"
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Database
db-init: ## Initialize database
	@echo "${BLUE}Initializing database...${NC}"
	@mkdir -p $(dir $(DB_PATH))
	$(UV) run -- $(PYTHON) -m promptriff.database.init

db-migrate: ## Run database migrations
	@echo "${BLUE}Running database migrations...${NC}"
	$(UV) run -- $(PYTHON) -m promptriff.database.migrate

db-backup: ## Backup database
	@echo "${BLUE}Backing up database...${NC}"
	@if [ -f $(DB_PATH) ]; then \
		cp $(DB_PATH) $(DB_PATH).backup.$$(date +%Y%m%d_%H%M%S); \
		echo "${GREEN}Database backed up successfully${NC}"; \
	else \
		echo "${RED}Database not found at $(DB_PATH)${NC}"; \
	fi

# Release
release: check build ## Build release version
	@echo "${BLUE}Building release version...${NC}"
	@echo "${GREEN}Release build complete${NC}"

package: release ## Create distributable package
	@echo "${BLUE}Creating distributable package...${NC}"
	$(UV) build --wheel
	@echo "${GREEN}Package created in dist/${NC}"

# Development utilities
shell: ## Start Python shell with project context
	@echo "${BLUE}Starting Python shell...${NC}"
	$(UV) run -- $(PYTHON) -i -c "from promptriff import *; print('PromptRiff shell ready')"

setup-dev: ## Set up development environment
	@echo "${BLUE}Setting up development environment...${NC}"
	@mkdir -p $(CONFIG_PATH)
	@if [ ! -f $(CONFIG_PATH)/config.yaml ]; then \
		cp examples/config.example.yaml $(CONFIG_PATH)/config.yaml; \
		echo "${GREEN}Created config file at $(CONFIG_PATH)/config.yaml${NC}"; \
	fi
	$(MAKE) install
	$(MAKE) db-init
	@echo "${GREEN}Development environment ready!${NC}"

run: ## Run the application
	@echo "${BLUE}Starting PromptRiff...${NC}"
	$(UV) run promptriff

# Documentation
docs: ## Generate documentation
	@echo "${BLUE}Generating documentation...${NC}"
	$(UV) run -- $(PYTHON) -m mkdocs build

docs-serve: ## Serve documentation locally
	@echo "${BLUE}Serving documentation...${NC}"
	$(UV) run -- $(PYTHON) -m mkdocs serve

# Utility targets
version: ## Show version information
	@echo "${BLUE}PromptRiff version information:${NC}"
	@grep version pyproject.toml | head -1 | cut -d '"' -f 2

deps-update: ## Update all dependencies
	@echo "${BLUE}Updating dependencies...${NC}"
	$(UV) sync --upgrade

deps-show: ## Show dependency tree
	@echo "${BLUE}Dependency tree:${NC}"
	$(UV) tree

# CI/CD helpers
ci-test: ## Run tests for CI
	$(UV) run pytest --cov=$(SRC_DIR) --cov-report=xml --cov-report=term

ci-lint: ## Run linting for CI
	$(UV) run ruff check --output-format=github $(SRC_DIR) $(TEST_DIR)
	$(UV) run mypy $(SRC_DIR) --junit-xml mypy-report.xml

# Installation helpers
install-user: build ## Install for current user
	@echo "${BLUE}Installing PromptRiff for current user...${NC}"
	$(UV) tool install .
	@echo "${GREEN}PromptRiff installed! Run 'promptriff' to start${NC}"

uninstall-user: ## Uninstall from current user
	@echo "${BLUE}Uninstalling PromptRiff...${NC}"
	$(UV) tool uninstall promptriff
	@echo "${GREEN}PromptRiff uninstalled${NC}"