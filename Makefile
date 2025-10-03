# Main Makefile for CI/CD and local development.
# Should be located in the project root.
SHELL := /bin/bash

.PHONY: help up down ps logs unit-test integration-test lint scan report

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  up                - Start services using Docker Compose."
	@echo "  down              - Stop and remove services."
	@echo "  ps                - List running services."
	@echo "  logs              - Follow logs for the main application."
	@echo "  unit-test         - Run fast unit tests with coverage."
	@echo "  integration-test  - Run integration tests against live services."
	@echo "  lint              - Run all code linters (flake8, bandit, yamllint)."
	@echo "  scan              - Scan Docker images for vulnerabilities with Trivy."
	@echo "  report            - Generate the HTML CI report."

# === Docker Compose Management ===
COMPOSE_FILES = -f infra/docker-compose.yml -f infra/docker-compose.override.yml
up:
	docker compose $(COMPOSE_FILES) up -d --wait --wait-timeout 180

down:
	docker compose $(COMPOSE_FILES) down -v

ps:
	docker compose $(COMPOSE_FILES) ps

logs:
	docker compose $(COMPOSE_FILES) logs -f app

# === Testing ===
unit-test:
	@echo "--- Running Unit Tests with Coverage ---"
	pytest --cov=backend --cov-report=xml --cov-report=html

integration-test:
	@echo "--- Running Integration Tests ---"
	pytest -q tests/integration/test_health_e2e.py

# === Code Quality & Security ===
lint:
	@echo "--- Running Linters ---"
	flake8 backend/
	bandit -r backend/ || true # Bandit is non-blocking
	yamllint infra/*.yml

scan:
	@echo "--- Scanning Docker Images ---"
	trivy image --exit-code 1 --severity HIGH,CRITICAL student-app:ci
	trivy image --exit-code 1 --severity HIGH,CRITICAL student-frontend:ci

# === Reporting ===
report:
	@echo "--- Generating CI Report ---"
	python .github/scripts/generate-report.py && echo "Report generated: ci-report.html"