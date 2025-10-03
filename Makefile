# Main Makefile for CI/CD and local development.
SHELL := /bin/bash

.PHONY: help up down ps logs unit-test integration-test lint scan report

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  up                - Start services with Docker Compose."
	@echo "  down              - Stop and remove services."
	@echo "  ps                - List running services."
	@echo "  logs              - Tail app logs."
	@echo "  unit-test         - Run fast unit tests (no services)."
	@echo "  integration-test  - Run E2E tests against live services."
	@echo "  lint              - Run flake8, bandit, yamllint."
	@echo "  scan              - Scan images with Trivy."
	@echo "  report            - Generate HTML CI repo

