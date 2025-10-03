# CI Cheatsheet

## Required repo secrets
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- *(optional)* `DB_SECRET` — multi-line `.env` for `infra/.env`

## Jobs (modular)
- **Quality Checks**: flake8, bandit (non-blocking), yamllint
- **Unit Tests**: pytest on `backend` code
- **Build & Scan**: docker buildx (cached) + Trivy scans
- **Infra Smoke + Integration**: compose up -> health checks -> Prometheus active targets -> E2E tests -> report

## Artifacts
- `compose.config.yaml`
- `ci-report.html`

## Local dev
```bash
cp .env.example infra/.env
make up
make test
make down
```
