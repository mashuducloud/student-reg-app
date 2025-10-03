SHELL := /bin/bash

.PHONY: help up down ps logs test lint scan report
help:
	@echo "Targets:"
	@echo "  up     - docker compose up (CI override)"
	@echo "  down   - docker compose down -v"
	@echo "  ps     - list services"
	@echo "  logs   - follow app logs"
	@echo "  test   - run integration tests"
	@echo "  lint   - flake8 + yamllint"
	@echo "  scan   - trivy scan local images"
	@echo "  report - generate simple CI HTML report"

up:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml up -d --wait --wait-timeout 180

down:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml down -v

ps:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml ps

logs:
	docker compose -f infra/docker-compose.yml -f infra/docker-compose.override.yml logs -f app

test:
	pytest -q tests/integration/test_health_e2e.py

lint:
	flake8 backend/ || true; yamllint infra/*.yml || true

scan:
	trivy image student-app:ci || true; trivy image student-frontend:ci || true

report:
	python .github/scripts/generate-report.py && echo "Open ./ci-report.html"
