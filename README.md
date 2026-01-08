# student-reg-app
Student Registration App Code

Here’s a version tailored to your current setup (Docker, OTEL, Prometheus, Tempo, Grafana, tests, etc.).

# Student Registration Service

A simple Flask-based **Student Registration API** instrumented with:

- **OpenTelemetry** (traces, logs, metrics)
- **Prometheus** (metrics)
- **Grafana + Tempo** (dashboards & traces)
- **MySQL** backend
- Fully Dockerised with `docker compose`

---

## Architecture

Services (from `infra/docker-compose.yml`):

- **app** → `student-app`
  Flask API + OTEL (traces/logs/metrics) + Prometheus metrics endpoint

- **mysql-db**
  MySQL 8.0 with schema initialised from `database/schema.sql`

- **otel-collector**
  OpenTelemetry Collector; receives OTLP data from the app and forwards to Tempo / Prometheus

- **tempo** → `infra-tempo`
  Trace storage (Grafana Tempo)

- **prometheus** → `infra-prometheus`
  Metrics scraping + storage

- **grafana** → `infra-grafana`
  Dashboards for metrics & traces

- **frontend** → `student-frontend`
  Simple frontend (optional UI) that talks to the API

- **tests** → `student-api-tests`
  Pytest container that runs API + DB tests with coverage

All services share the `observability-network` Docker network.

---

## Prerequisites

- Docker & Docker Compose
- (Optional) Python + venv if you want to run things locally without Docker

---

## How to run everything

From the `infra/` directory:

```bash
# Start all services in the background
docker compose up -d


To rebuild the backend app image after code changes:

docker compose build app
docker compose up -d


To stop everything:

docker compose down

Ports

Student API (Flask): http://localhost:5000

Frontend: http://localhost:8080

Prometheus: http://localhost:9091 (proxied to container’s 9090)

Grafana: http://localhost:3300 (user/pass: admin / admin)

Tempo (HTTP UI / API): http://localhost:3201/metrics (http://localhost:3201)

OTLP gRPC (collector): localhost:43171 → forwarded to collector’s 4317

App metrics (Prometheus /metrics): http://localhost:9100/metrics

Environment variables

Most behaviour is controlled via .env and environment variables.

Database (used by config.DB_CONFIG)

Typical vars:

DB_HOST=mysql-db
DB_PORT=3306
DB_NAME=students
DB_USER=root
DB_PASSWORD=yourpassword


In Docker, DB_HOST must be mysql-db (the service name), not localhost.

Observability
# Service identity
SERVICE_NAME=student-registration-service

# OTLP endpoint (used for traces + logs)
OTEL_EXPORTER_OTLP_ENDPOINT=otel-collector:4317

# Tracing
ENABLE_CONSOLE_SPANS=false   # true = also print spans to stdout

# Logging
LOG_LEVEL=INFO
ENABLE_CONSOLE_LOG_EXPORTER=true   # OTel logs → stdout
ENABLE_OTLP_LOG_EXPORTER=true      # OTel logs → OTLP (collector)

# Metrics / Prometheus
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9100


The app reads these at startup in main.py and configures OTEL accordingly.

Healthcheck

The app exposes:

GET /health


Returns 200 and {"status": "healthy"} if:

The API is up, and

The app can successfully connect to MySQL.

Docker healthcheck for student-app runs:

healthcheck:
  test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:5000/health || exit 1"]


If DB is misconfigured or down, /health returns 500 and the container becomes unhealthy.

Testing

Tests are run inside a dedicated container to match the production image.

From infra/:

docker compose run --rm tests


This will:

Start a temporary container based on the backend image

Run pytest test_app.py --cov=. --cov-report=term-missing -v

Print coverage (e.g. ~86% currently)

You can also run pytest locally if you want:

cd backend
pytest test_app.py --cov=. --cov-report=term-missing -v


(Assuming you have a local venv with requirements.txt installed.)

Observability
1. Traces

The app uses OpenTelemetry to create spans for:

Incoming HTTP requests (/, /health, /register)

DB connections (create_db_connection)

Student inserts (db_insert_student)

Traces are exported via OTLP gRPC to the collector at:

OTEL_EXPORTER_OTLP_ENDPOINT (default: otel-collector:4317 inside Docker)

View traces in Grafana via Tempo:

Open Grafana: http://localhost:3300

Log in with admin / admin

Add Tempo as a data source if not already configured:

Type: Tempo

URL: http://tempo:3200

Use Explore → Tempo to search for traces:

Filter by service.name = student-registration-service

Or by span name: HTTP POST /register, db_insert_student, etc.

Hit the API a few times (e.g. curl -X POST http://localhost:5000/register ...) and traces should appear.

2. Metrics

The app exposes metrics via OTEL → Prometheus:

PrometheusMetricReader is configured when ENABLE_PROMETHEUS=true.

start_http_server(PROMETHEUS_PORT) exposes /metrics (default port 9100).

Example app metric:

student_registration_requests_total
Counter incremented on every incoming HTTP request.

View metrics in Prometheus:

Open Prometheus: http://localhost:9091

In the “Expression” box, try:

student_registration_requests_total

rate(student_registration_requests_total[1m])

In Grafana:

Add Prometheus as data source:

Type: Prometheus

URL: http://prometheus:9090

Create a dashboard panel:

Query: rate(student_registration_requests_total[5m])

Visualise as a time series of request rate.

3. Logs

Standard Python logging is configured with logging.basicConfig.

OpenTelemetry logging pipeline is set up with:

LoggerProvider(resource=resource)

ConsoleLogExporter (to stdout, optional via env)

OTLPLogExporter (to collector, optional / version-guarded)

Typical log usage:

log.info("Student registered successfully", extra={"email": email})
log.error("Database connection failed", extra={"db.error": str(e)})


Logs emitted inside spans will carry trace ID / span ID, allowing log–trace correlation in downstream backends (if your OTEL collector forwards logs to something like Loki or a logging system).

Running on AWS EC2 (free tier)

You can reuse this stack on a small EC2 instance:

Use the same docker compose setup, or

Run the app container + OTEL collector only, and use managed services for:

Metrics/logs (e.g. CloudWatch)

Traces (e.g. X-Ray or managed Tempo/Grafana)

Recommendations:

Keep ENABLE_CONSOLE_SPANS=false in production to avoid noisy logs.

Tune log level (LOG_LEVEL=INFO or WARNING).

Consider using gunicorn instead of Flask’s dev server as the container entrypoint.

Quick dev commands

From infra/:

# Start everything
docker compose up -d

# Tail app logs
docker logs -f student-app

# Run tests
docker compose run --rm tests

# Stop everything
docker compose down

🎓 Student Registration System (Full Observability Stack)

A production-grade Flask + MySQL web application with OpenTelemetry, Prometheus, Tempo, and Grafana integration for full observability.

This project demonstrates a modern, instrumented microservice setup with metrics, traces, and logs — all running locally with Docker Compose.

🧱 Architecture Overview

Services included:

Service	Purpose
🐍 student-app	Flask backend API (Gunicorn, OpenTelemetry)
🧪 student-api-tests	Pytest-based integration test runner
🗄️ mysql-db	MySQL database for student data
📈 prometheus	Metrics collection and scraping
🔭 tempo	Distributed tracing backend
📊 grafana	Visualization dashboards for metrics & traces
🧩 otel-collector	OpenTelemetry collector (receives spans/logs)

All services run together via Docker Compose on a shared internal network.

⚙️ Tech Stack
Component	Technology
Backend	Flask (Python 3.11)
Database	MySQL
Server	Gunicorn (WSGI)
Observability	OpenTelemetry SDK, Prometheus, Tempo, Grafana
Metrics Export	Prometheus HTTP exporter (via prometheus_client)
Tracing	OTLP → OpenTelemetry Collector → Tempo
Logging	Console JSON + OTLP structured logs
Container Orchestration	Docker Compose
🧩 Key Features

✅ Environment-driven configuration (.env)
✅ Health endpoint for Docker & Prometheus
✅ Automatic DB connection tracing
✅ Prometheus metrics (/metrics endpoint on port 9100)
✅ Distributed tracing via OTEL Collector → Tempo → Grafana
✅ Structured JSON logs exported via OTLP
✅ Gunicorn for production-grade serving
✅ Multi-stage Docker build (small, secure, non-root runtime)
✅ Ready-to-run local observability stack

🗂️ Project Structure
student-reg-app/
├── backend/
│   ├── main.py                # Flask app + instrumentation
│   ├── config.py              # DB connection config
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Multi-stage, non-root image
│
├── infra/
│   ├── docker-compose.yml     # Orchestrates all services
│   ├── prometheus.yml         # Prometheus scrape config
│   ├── tempo.yaml             # Tempo configuration
│   └── .env                   # Environment variables
│
└── README.md

🚀 Running Locally
1️⃣ Prerequisites

Docker & Docker Compose installed

(Optional) Python 3.11+ for local testing

2️⃣ Start everything

From the infra/ directory:

docker compose up -d --build


This will:

Start the MySQL DB and initialize the schema

Launch Flask backend under Gunicorn

Start OTEL Collector, Prometheus, Tempo, and Grafana

Expose metrics, traces, and dashboards





🎓 Student Registration Service (Full Observability Stack)

A production-grade Flask + MySQL web application instrumented with:

OpenTelemetry — Traces, Logs, and Metrics

Prometheus — Metrics collection

Tempo — Distributed tracing backend

Grafana — Unified dashboards for metrics and traces

MySQL — Persistent student data storage

Pytest — Containerized integration tests

Gunicorn — Production WSGI server

Fully Dockerized and environment-driven

🧱 Architecture Overview
Service	Description
🐍 student-app	Flask backend API (Gunicorn, OpenTelemetry, Prometheus metrics exporter)
🧪 student-api-tests	Pytest-based integration test runner
🗄️ mysql-db	MySQL 8.0 database (schema initialized from database/schema.sql)
📈 prometheus	Collects metrics from the backend and stores time series
🔭 tempo	Receives and stores OpenTelemetry traces
📊 grafana	Visualizes metrics and traces from Prometheus and Tempo
🧩 otel-collector	OpenTelemetry Collector: receives OTLP data (traces/logs/metrics) from the app
🌐 student-frontend	Optional frontend UI that calls the Flask API

All containers share a common Docker network: observability-network.

⚙️ Tech Stack
Component	Technology
Backend	Flask (Python 3.11)
Database	MySQL 8.0
Server	Gunicorn (WSGI)
Instrumentation	OpenTelemetry SDK
Metrics Export	Prometheus HTTP Exporter
Tracing	OTLP → OpenTelemetry Collector → Tempo
Visualization	Grafana
Containerization	Docker + Docker Compose
Testing	Pytest in container
✅ Key Features

Environment-driven configuration via .env

/health endpoint for liveness & readiness

Automatic DB connection tracing

Prometheus metrics exporter (/metrics on port 9100)

Full trace propagation via OpenTelemetry

Structured logs (console + OTLP exporter)

Gunicorn for concurrent, production-grade serving

Multi-stage, non-root Docker image

Turnkey observability stack via Docker Compose

🗂️ Project Structure
student-reg-app/
├── backend/
│   ├── main.py                # Flask app + OpenTelemetry instrumentation
│   ├── config.py              # DB config loader (reads from env)
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Multi-stage, non-root runtime
│
├── infra/
│   ├── docker-compose.yml     # Defines all observability services
│   ├── prometheus.yml         # Prometheus scrape targets
│   ├── tempo.yaml             # Tempo configuration
│   └── .env                   # Environment variables
│
└── README.md

🚀 Running Locally
1️⃣ Prerequisites

Docker & Docker Compose

(Optional) Python 3.11+ if you want to run locally outside Docker

2️⃣ Start everything

From the infra/ directory:

docker compose up -d --build


This will:

Start MySQL and initialize schema

Launch Flask backend under Gunicorn

Start OTEL Collector, Prometheus, Tempo & Grafana

Expose all metrics, traces & dashboards

3️⃣ Stop everything
docker compose down

🌍 Service Endpoints
Service	URL	Description
API (Flask)	http://localhost:5000
	Main backend service
Healthcheck	http://localhost:5000/health
	Reports DB connectivity
Frontend (UI)	http://localhost:8080
	Optional frontend app
Prometheus	http://localhost:9091
	Metrics dashboard (proxy to :9090)
Grafana	http://localhost:3300
	Dashboards (admin / admin)
Tempo	http://localhost:3201
	Trace storage + API
Prometheus /metrics	http://localhost:9100/metrics
	Student-app metrics endpoint
OTLP gRPC	localhost:43171	OTEL Collector endpoint
⚙️ Environment Variables

Main settings are defined in infra/.env.

🗄️ Database
DB_HOST=mysql-db
DB_PORT=3306
DB_NAME=student_registration_db
DB_USER=student
DB_PASSWORD="Barcelona@1819"

MYSQL_DATABASE=student_registration_db
MYSQL_USER=student
MYSQL_PASSWORD="Barcelona@1819"
MYSQL_ROOT_PASSWORD="Barcelona@1819"
MYSQL_ROOT_HOST=%

🧠 OpenTelemetry / Observability
SERVICE_NAME=student-registration-service
OTEL_EXPORTER_OTLP_ENDPOINT=otel-collector:4317
ENABLE_CONSOLE_SPANS=false
LOG_LEVEL=INFO
ENABLE_CONSOLE_LOG_EXPORTER=true
ENABLE_OTLP_LOG_EXPORTER=true
ENABLE_PROMETHEUS=true
PROMETHEUS_PORT=9100

⚙️ Flask Runtime
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000

❤️ Healthcheck

Endpoint:

GET /health


Returns:

{"status": "healthy"}


Status 200 = API up + DB connected

Status 500 = DB unreachable

Docker uses:

healthcheck:
  test: ["CMD-SHELL", "curl -fsS http://127.0.0.1:5000/health || exit 1"]

🔍 Observability
1️⃣ Traces

Every HTTP request (/, /health, /register) is traced.

DB operations (create_db_connection, db_insert_student) are captured as child spans.

Exported via OTLP → Collector → Tempo.

View in Grafana:

Open http://localhost:3300
 (login admin/admin)

Add Tempo data source (URL http://tempo:3200)

Explore → Tempo → search service.name=student-registration-service

Send requests to POST /register and watch traces appear.

2️⃣ Metrics

Prometheus scrapes /metrics (Port 9100).

Metric example:

student_registration_requests_total


Counts each incoming HTTP request.

View:

Prometheus UI http://localhost:9091
 → query:

rate(student_registration_requests_total[1m])


Grafana → Add Prometheus source (URL http://prometheus:9090)
→ create panel with the same query to visualize request rate.

3️⃣ Logs

Python logging integrated with OpenTelemetry:

log.info("Student registered", extra={"email": email})
log.error("DB failed", extra={"db.error": str(e)})


Console + OTLP exporters enabled via env.

Logs carry trace and span IDs for correlation in Grafana (if Loki is added).

🧪 Testing

Run tests in container:

docker compose run --rm student-api-tests


Equivalent local run:

cd backend
pytest test_app.py --cov=. --cov-report=term-missing -v


Outputs coverage report (typically > 85%).

☁️ Running on AWS EC2 / Cloud

You can deploy this stack unchanged:

Run docker compose up -d on EC2.

Or deploy only student-app + otel-collector and send data to managed Grafana Cloud, Tempo, or CloudWatch.

Tips:

Keep ENABLE_CONSOLE_SPANS=false in production.

Adjust LOG_LEVEL and GUNICORN_WORKERS for load.

🛠️ Quick Commands
# Start everything
docker compose up -d

# Tail app logs
docker logs -f student-app

# Run tests
docker compose run --rm student-api-tests

# Stop everything
docker compose down

🔒 Security & Production Hardening

Non-root user inside container

Multi-stage Docker build → smaller attack surface

TLS certificates installed for outbound HTTPS

Configurable Gunicorn concurrency

Sensitive credentials externalized via .env

🧠 Next Steps

 Add Grafana dashboards for Prometheus and Tempo

 Integrate Loki for structured log visualization

 Add CI/CD pipeline (GitHub Actions / AWS CodeBuild)

 Add frontend UI for student registration flow

🧾 License

MIT License © 2025 — Student Registration Service
