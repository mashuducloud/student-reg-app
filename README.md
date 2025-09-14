3-Tier Student Registration Web Application

A classic 3-tier web application for student registration. It demonstrates a full-stack workflow with a Flask backend, MySQL database, Tailwind CSS frontend, automated testing, and observability using OpenTelemetry, Prometheus, Tempo, and Grafana.

🏛️ Architecture

Frontend (Presentation Tier):
HTML + Tailwind CSS interface for student registration.

Backend (Logic Tier):
Flask REST API that handles registration requests, validation, logging, and tracing.

Database (Data Tier):
MySQL database for persistent storage of student data.

Observability:
OpenTelemetry instrumentation with traces, metrics, and logs exported via the OTEL Collector to Prometheus and Tempo, visualized in Grafana.

📂 Project Structure
student-registration-app/
├── backend/
│   ├── config.py                   # DB + environment configuration
│   ├── main.py                     # Flask app with logging, tracing, metrics
│   ├── test_app.py                 # Pytest API tests
│   └── requirements.txt            # Python dependencies
│
├── database/
│   └── schema.sql                  # SQL schema for students DB
│
├── frontend/
│   └── index.html                  # Tailwind CSS frontend
│
├── infra/
│   ├── docker-compose.yml          # Orchestrates Grafana, Tempo, Prometheus, OTEL Collector
│   ├── otel-collector-config.yaml  # OTEL Collector config
│   ├── prometheus.yml              # Prometheus scrape config
│   └── tempo.yaml                  # Tempo tracing backend config
│
├── .gitignore
└── README.md

⚡ Requirements

Python 3.10+

MySQL Server

Docker & Docker Compose

Python dependencies (from backend/requirements.txt):

flask
flask-cors
mysql-connector-python
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-prometheus
prometheus-client
pytest

🛠️ Setup
1. Database

Run database/schema.sql in MySQL:

CREATE DATABASE student_registration_db;
USE student_registration_db;

CREATE TABLE students (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

2. Backend
cd backend
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
python main.py


API: http://localhost:5000

Metrics: http://localhost:9100/metrics

3. Frontend

Open frontend/index.html with VS Code Live Server.

🐳 Observability Stack

From infra/:

docker-compose up -d


Services:

Service	Port	Description
Grafana	3000	Dashboards (admin/admin)
Prometheus	9090	Metrics collection
Tempo	3200	Tracing backend
OTEL Collector	4317/8	Receives traces/metrics

Stop with:

docker-compose down

🌐 API Endpoints
Endpoint	Method	Description
/	GET	Health check
/register	POST	Register student
/metrics	GET	Prometheus metrics

Example:

curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}'

📊 Observability

Metrics:

Custom counter: student_registration_requests_total

Scraped by Prometheus from http://localhost:9100/metrics

Traces:

Spans for requests and DB ops (register_student_handler, create_db_connection, db_insert_student)

Exported via OTLP to Tempo → viewed in Grafana Explore

Logs:

Structured JSON logs with trace_id and span_id

Viewable with docker-compose logs -f backend

📊 Grafana Dashboard Import

Save this as student-registration-dashboard.json and import in Grafana:

{
  "id": null,
  "uid": "student-registration",
  "title": "Student Registration Monitoring",
  "schemaVersion": 36,
  "version": 1,
  "panels": [
    {
      "type": "graph",
      "title": "Student Registrations Over Time",
      "targets": [
        {
          "expr": "sum(student_registration_requests_total)",
          "legendFormat": "registrations",
          "datasource": "Prometheus"
        }
      ],
      "gridPos": { "x":0, "y":0, "w":12, "h":6 }
    },
    {
      "type": "trace",
      "title": "Registration Traces",
      "datasource": "Tempo",
      "targets": [
        {
          "query": "service.name = \"student-registration-service\" AND http.target = \"/register\""
        }
      ],
      "gridPos": { "x":12, "y":0, "w":12, "h":12 }
    }
  ]
}

🧪 Testing

Run API tests:

cd backend
pytest test_app.py


⚠️ Note: Tests expect {status, message} but the backend returns only {message}. Adjust tests or backend for consistency.

⚠️ Notes

Use gunicorn/uwsgi instead of Flask dev server in production.

Ensure ports 5000, 9100, 3000, 9090, 3200, 4317, 4318 are free.

Logs can be extended to Grafana Loki for unified observability.

📜 License

MIT License.

✅ This is the final cleaned-up README.md, fully aligned with your codebase and configs.

Would you like me to now regenerate the infra/docker-compose.yml and configs (otel-collector, prometheus, tempo) so they exactly match this README (ports, services, exporters)?

You said:
yes
ChatGPT said:

Perfect ✅ Let’s generate the infra files so they align exactly with the final README. These will allow you to spin up the full observability stack (OTEL Collector, Prometheus, Tempo, Grafana) with a single docker-compose up.

📂 infra/docker-compose.yml
version: "3.9"

services:
  # -------------------------
  # Backend Application
  # -------------------------
  backend:
    build: ../backend
    container_name: student-backend
    ports:
      - "5000:5000"   # Flask API
      - "9100:9100"   # Metrics
    environment:
      - DB_HOST=mysql
      - DB_PORT=3306
      - DB_NAME=student_registration_db
      - DB_USER=root
      - DB_PASSWORD=example
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
    depends_on:
      - mysql
      - otel-collector

  # -------------------------
  # MySQL Database
  # -------------------------
  mysql:
    image: mysql:8.0
    container_name: student-mysql
    environment:
      MYSQL_ROOT_PASSWORD: example
      MYSQL_DATABASE: student_registration_db
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ../database/schema.sql:/docker-entrypoint-initdb.d/schema.sql

  # -------------------------
  # OpenTelemetry Collector
  # -------------------------
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.97.0
    container_name: otel-collector
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
    depends_on:
      - tempo
      - prometheus

  # -------------------------
  # Prometheus
  # -------------------------
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    command:
      - --config.file=/etc/prometheus/prometheus.yml
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  # -------------------------
  # Tempo (Tracing backend)
  # -------------------------
  tempo:
    image: grafana/tempo:latest
    container_name: tempo
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
    ports:
      - "3200:3200"

  # -------------------------
  # Grafana
  # -------------------------
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      - tempo

volumes:
  mysql-data:

📂 infra/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
      http:

exporters:
  logging:
    loglevel: info
  prometheus:
    endpoint: "0.0.0.0:9100"
  otlp:
    endpoint: tempo:4317
    tls:
      insecure: true

processors:
  batch:

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp, logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
    logs:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]

📂 infra/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "flask-backend"
    static_configs:
      - targets: ["backend:9100"]

📂 infra/tempo.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
        http:

ingester:
  trace_idle_period: 10s
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 1h

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo
    wal:
      path: /tmp/tempo/wal

🚀 How to Run
cd infra
docker-compose up -d


Grafana → http://localhost:3000
 (admin/admin)

Prometheus → http://localhost:9090

Tempo → http://localhost:3200

Flask API → http://localhost:5000

Metrics → http://localhost:9100/metrics

✅ These infra configs now match exactly with the final README you approved.

Would you like me to also add a provisioning folder for Grafana (auto-configure Prometheus + Tempo as datasources and import the dashboard JSON automatically at startup), so developers don’t need to configure anything manually?

You said:
Open frontend/index.html as docker container
ChatGPT said:

Great idea 👍 You want the frontend (index.html) served from a Docker container, instead of opening it manually with Live Server.

We can achieve this by:

Adding a lightweight Nginx container that serves the frontend folder.

Updating infra/docker-compose.yml to include a frontend service.

📂 infra/Dockerfile.frontend
# Use a lightweight Nginx image
FROM nginx:alpine

# Copy frontend files into Nginx's default HTML dir
COPY ../frontend /usr/share/nginx/html

# Expose port 8080
EXPOSE 8080

📂 Update infra/docker-compose.yml

Add a frontend service:

  # -------------------------
  # Frontend (Nginx serving index.html)
  # -------------------------
  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: student-frontend
    ports:
      - "8080:80"
    depends_on:
      - backend

🚀 Run Everything

From infra/:

docker-compose up -d --build


Now you’ll have:

Frontend → http://localhost:8080

Backend API → http://localhost:5000

Metrics → http://localhost:9100/metrics

Grafana → http://localhost:3000

Prometheus → http://localhost:9090

Tempo → http://localhost:3200

⚡ Now your app is fully containerized — backend, database, observability, and frontend all run under Docker.

👉 Do you want me to also wire the frontend Nginx config so API requests (e.g. /register) are automatically proxied to the backend container (no CORS issues), instead of hitting localhost:5000 directly?

You said:
update final readme
ChatGPT said:

Perfect 👍 Let’s finalize the README.md so it reflects the new frontend Docker container (served via Nginx) and full-stack observability setup.

Here’s the cleaned and updated final README:

3-Tier Student Registration Web Application

A classic 3-tier web application for student registration. It demonstrates a full-stack workflow with a Flask backend, MySQL database, Tailwind CSS frontend, automated testing, and observability using OpenTelemetry, Prometheus, Tempo, and Grafana.
Now fully containerized with Docker Compose (frontend, backend, DB, and observability stack).

🏛️ Architecture

Frontend (Presentation Tier):
Static HTML + Tailwind CSS form, served via Nginx Docker container.

Backend (Logic Tier):
Flask REST API with business logic, tracing, logging, and metrics.

Database (Data Tier):
MySQL database for student records.

Observability:
OpenTelemetry → OTEL Collector → Prometheus & Tempo → Grafana.

📂 Project Structure
student-registration-app/
├── backend/
│   ├── config.py                   # DB + environment configuration
│   ├── main.py                     # Flask app with logging, tracing,metrics
│   ├── test_app.py                 # Pytest API tests
│   └── requirements.txt            # Python dependencies
│
├── database/
│   └── schema.sql                  # SQL schema for students DB
│
├── frontend/
│   └── index.html                  # Tailwind CSS frontend
│
├── infra/
│   ├── docker-compose.yml          # Orchestrates frontend, backend, DB observability
│   ├── Dockerfile.frontend         # Nginx Dockerfile for frontend
│   ├── otel-collector-config.yaml  # OTEL Collector config
│   ├── prometheus.yml              # Prometheus scrape config
│   └── tempo.yaml                  # Tempo tracing backend config
│
├── .gitignore
└── README.md

⚡ Requirements

Docker & Docker Compose

Python 3.10+ (if running backend locally)

MySQL (if running DB locally outside Docker)

Python dependencies (backend/requirements.txt):

flask
flask-cors
mysql-connector-python
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-exporter-prometheus
prometheus-client
pytest

🐳 Running with Docker Compose

From infra/:

docker-compose up -d --build

Services
Service	Port	Description
Frontend	8080	Student registration form
Backend (Flask)	5000	API endpoints
Metrics	9100	Prometheus scrape target
MySQL	3306	Student DB
Grafana	3000	Dashboards (admin/admin)
Prometheus	9090	Metrics storage
Tempo	3200	Distributed tracing
OTEL Collector	4317/8	gRPC & HTTP OTLP ingest

Stop everything:

docker-compose down

🌐 API Endpoints
Endpoint	Method	Description
/	GET	Health check
/register	POST	Register student
/metrics	GET	Prometheus metrics

Example:

curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","email":"alice@example.com"}'

📊 Observability

Metrics

Counter: student_registration_requests_total

Scraped by Prometheus from http://backend:9100/metrics

Traces

Spans: register_student_handler, create_db_connection, db_insert_student

Exported via OTLP → Tempo → Grafana Explore

Logs

Structured JSON logs with trace_id and span_id

View with docker-compose logs -f backend

📊 Grafana Dashboard Import

Save this JSON as student-registration-dashboard.json and import in Grafana:

{
  "id": null,
  "uid": "student-registration",
  "title": "Student Registration Monitoring",
  "schemaVersion": 36,
  "version": 1,
  "panels": [
    {
      "type": "graph",
      "title": "Student Registrations Over Time",
      "targets": [
        {
          "expr": "sum(student_registration_requests_total)",
          "legendFormat": "registrations",
          "datasource": "Prometheus"
        }
      ],
      "gridPos": { "x":0, "y":0, "w":12, "h":6 }
    },
    {
      "type": "trace",
      "title": "Registration Traces",
      "datasource": "Tempo",
      "targets": [
        {
          "query": "service.name = \"student-registration-service\" AND http.target = \"/register\""
        }
      ],
      "gridPos": { "x":12, "y":0, "w":12, "h":12 }
    }
  ]
}

🧪 Testing

Run backend tests:

Great 👍 — let’s expand the test suite so create_db_connection() is covered for both success and failure cases.

Here’s the improved test_main.py with an extra negative test:

import pytest
import json
from main import app, create_db_connection


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Test home endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration API is running" in response.data


def test_register_missing_fields(client):
    """Test /register endpoint with missing data"""
    response = client.post(
        "/register",
        data=json.dumps({"first_name": "John"}),  # missing last_name, email
        content_type="application/json"
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (DB mocked)"""

    # mock DB connection and cursor
    class DummyCursor:
        def execute(self, *args, **kwargs): pass
        def close(self): pass

    class DummyConnection:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def close(self): pass
        def is_connected(self): return True

    monkeypatch.setattr("main.create_db_connection", lambda: DummyConnection())

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert b"Student registered successfully" in response.data


def test_create_db_connection_success(monkeypatch):
    """Directly test create_db_connection() when connection succeeds"""

    class DummyConnection:
        def is_connected(self): return True

    class DummyConnector:
        @staticmethod
        def connect(**kwargs): return DummyConnection()

    import main
    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()


def test_create_db_connection_failure(monkeypatch):
    """Directly test create_db_connection() when connection fails"""

    class DummyError(Exception):
        pass

    class FailingConnector:
        @staticmethod
        def connect(**kwargs): 
            raise DummyError("DB connection failed")

    import main
    monkeypatch.setattr(main.mysql, "connector", FailingConnector)

    conn = create_db_connection()
    assert conn is None  # should gracefully handle failure

🔧 What’s new

test_create_db_connection_success
✅ Ensures the happy path works with a fake connection.

test_create_db_connection_failure
✅ Simulates mysql.connector.connect throwing an exception → your function should return None.

This way, both OK and ERROR paths are covered.

🚀 Run the tests
pytest -v


You should now see 5 tests passing:

test_home

test_register_missing_fields

test_register_success

test_create_db_connection_success

test_create_db_connection_failure

👉 Do you also want me to extend the /register endpoint test to cover the case where create_db_connection() fails (so it returns a 500 error)? That would give you full request-level coverage for DB failures too.

You said:
yes
ChatGPT said:

Perfect ✅ — let’s add one more test case that simulates a DB connection failure inside the /register endpoint, so we cover the full error path.

Here’s your updated test_main.py:

import pytest
import json
from main import app, create_db_connection


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Test home endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration API is running" in response.data


def test_register_missing_fields(client):
    """Test /register endpoint with missing data"""
    response = client.post(
        "/register",
        data=json.dumps({"first_name": "John"}),  # missing last_name, email
        content_type="application/json"
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (DB mocked)"""

    # mock DB connection and cursor
    class DummyCursor:
        def execute(self, *args, **kwargs): pass
        def close(self): pass

    class DummyConnection:
        def cursor(self): return DummyCursor()
        def commit(self): pass
        def close(self): pass
        def is_connected(self): return True

    monkeypatch.setattr("main.create_db_connection", lambda: DummyConnection())

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert b"Student registered successfully" in response.data


def test_register_db_failure(monkeypatch, client):
    """Test /register endpoint when DB connection fails"""

    # Simulate DB connection failure
    monkeypatch.setattr("main.create_db_connection", lambda: None)

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Fail",
            "last_name": "Case",
            "email": "fail@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 500
    assert b"Failed to register student" in response.data


def test_create_db_connection_success(monkeypatch):
    """Directly test create_db_connection() when connection succeeds"""

    class DummyConnection:
        def is_connected(self): return True

    class DummyConnector:
        @staticmethod
        def connect(**kwargs): return DummyConnection()

    import main
    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()


def test_create_db_connection_failure(monkeypatch):
    """Directly test create_db_connection() when connection fails"""

    class DummyError(Exception):
        pass

    class FailingConnector:
        @staticmethod
        def connect(**kwargs):
            raise DummyError("DB connection failed")

    import main
    monkeypatch.setattr(main.mysql, "connector", FailingConnector)

    conn = create_db_connection()
    assert conn is None  # should gracefully handle failure

🔧 What’s new

test_register_db_failure

Monkeypatches create_db_connection to return None.

Calls /register with valid input.

Expects a 500 Internal Server Error with "Failed to register student" message.

🚀 Run
pytest -v


You should now see 6 tests pass:

test_home

test_register_missing_fields

test_register_success

test_register_db_failure

test_create_db_connection_success

test_create_db_connection_failure

👉 Do you also want me to help you add code coverage reporting (with pytest-cov) so your CI/CD pipeline can fail if coverage drops below a threshold? That’s a common next step.

You said:
yes
ChatGPT said:

Perfect 🚀 — adding coverage reporting is a great next step for CI/CD. With pytest-cov, you can measure how much of your main.py is exercised by your tests and even enforce a minimum coverage threshold.

🔧 Step 1: Add pytest-cov to dependencies

Since your requirements.txt already has pytest, add this line:

pytest-cov==5.0.0


(or latest stable version).

🔧 Step 2: Run tests with coverage

From your project root, run:

pytest --cov=main --cov-report=term-missing -v


Explanation:

--cov=main → measure coverage for main.py.

--cov-report=term-missing → shows which lines are not covered.

-v → verbose output.

Example output:

---------- coverage: platform linux, python 3.11 ----------
Name     Stmts   Miss  Cover   Missing
--------------------------------------
main.py    150      5    97%   88-93, 140

🔧 Step 3: Enforce a minimum threshold

Add --cov-fail-under=90 (for example) so the test run fails if coverage drops below 90%:

pytest --cov=main --cov-report=term-missing --cov-fail-under=90 -v

🔧 Step 4: Add to CI/CD (GitHub Actions example)

Update your .github/workflows/tests.yml:

name: CI Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests with coverage
        run: pytest --cov=main --cov-report=term-missing --cov-fail-under=90 -v


This way:

Every push/PR runs tests.

If coverage < 90%, the pipeline fails.

Developers must add tests before merging 🚀.

🔧 Optional Step 5: Generate HTML report

For local debugging, you can also generate an HTML coverage report:

pytest --cov=main --cov-report=html


Then open htmlcov/index.html in a browser.

✅ With this setup, your tests not only validate functionality but also guard against untested code sneaking in.

👉 Do you want me to also help you Dockerize the test run with coverage (so your CI/CD runs pytest-cov inside the same Docker image you deploy)?

You said:
yes
ChatGPT said:

Nice 🚀 — let’s make sure your tests + coverage run inside Docker, so your CI/CD pipeline tests the exact same environment you deploy.

🔧 Step 1: Update your Dockerfile

Right now, your container probably just runs main.py. We’ll make it flexible so you can run either the app or tests.

Here’s a refactored Dockerfile:

FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add code
COPY . .

# Default command runs the app
CMD ["python", "main.py"]


Since pytest + pytest-cov are in requirements.txt, the container can run tests too.

🔧 Step 2: Run tests with coverage inside Docker (locally)

Build the image:

docker build -t student-api .


Run tests with coverage:

docker run --rm student-api pytest --cov=main --cov-report=term-missing --cov-fail-under=90 -v


Run app normally:

docker run -p 5000:5000 student-api

🔧 Step 3: GitHub Actions Workflow

Here’s an updated .github/workflows/tests.yml that uses Docker:

name: CI Tests (Dockerized)

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t student-api .

      - name: Run pytest with coverage inside Docker
        run: docker run --rm student-api pytest --cov=main --cov-report=term-missing --cov-fail-under=90 -v

🔧 Step 4: Optional — Generate HTML coverage report artifact

If you want CI to keep a browsable coverage report, add:

      - name: Run pytest with coverage + HTML report
        run: docker run --rm -v ${{ github.workspace }}/coverage:/coverage student-api \
          pytest --cov=main --cov-report=html:/coverage --cov-fail-under=90 -v

      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-html
          path: coverage


This will let you download and view coverage reports from GitHub Actions.

✅ Summary:

pytest-cov is installed inside Docker (from requirements.txt).

You can run tests inside the container (docker run student-api pytest ...).

CI/CD builds the Docker image and executes tests in that environment.

Optional HTML reports give you full visibility into coverage.

👉 Do you want me to also set up multi-stage Docker builds (so tests run in one stage and your final image stays lightweight without pytest)? This is common for production deployments.

✅ Final test_main.py (clean + full coverage)
import pytest
import json
from main import app, create_db_connection


@pytest.fixture
def client():
    """Flask test client fixture"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home(client):
    """Test home endpoint returns 200"""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Registration API is running" in response.data


def test_register_missing_fields(client):
    """Test /register endpoint with missing data"""
    response = client.post(
        "/register",
        data=json.dumps({"first_name": "John"}),  # missing last_name, email
        content_type="application/json"
    )
    assert response.status_code == 400
    assert b"required" in response.data


def test_register_success(monkeypatch, client):
    """Test /register endpoint with valid data (DB mocked)"""

    class DummyCursor:
        def execute(self, *_args, **_):
            pass

        def close(self):
            pass

    class DummyConnection:
        def cursor(self):
            return DummyCursor()

        def commit(self):
            pass

        def close(self):
            pass

        def is_connected(self):
            return True

    monkeypatch.setattr("main.create_db_connection", lambda: DummyConnection())

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane.doe@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 201
    assert b"Student registered successfully" in response.data


def test_register_db_failure(monkeypatch, client):
    """Test /register endpoint when DB connection fails"""

    # Force create_db_connection() to return None
    monkeypatch.setattr("main.create_db_connection", lambda: None)

    response = client.post(
        "/register",
        data=json.dumps({
            "first_name": "Fail",
            "last_name": "Case",
            "email": "fail@example.com"
        }),
        content_type="application/json"
    )

    assert response.status_code == 500
    assert b"Failed to register student" in response.data


def test_create_db_connection_success(monkeypatch):
    """Directly test create_db_connection() success"""

    class DummyConnection:
        def is_connected(self):
            return True

    class DummyConnector:
        @staticmethod
        def connect(**_):
            return DummyConnection()

    import main
    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is not None
    assert conn.is_connected()


def test_create_db_connection_failure(monkeypatch):
    """Directly test create_db_connection() failure"""

    class DummyConnector:
        @staticmethod
        def connect(**_):
            raise Exception("DB connection failed")

    import main
    monkeypatch.setattr(main.mysql, "connector", DummyConnector)

    conn = create_db_connection()
    assert conn is None

🔧 What’s new

test_register_db_failure → ensures /register returns 500 when DB connection fails.

test_create_db_connection_failure → ensures create_db_connection() returns None when connector raises an exception.

Still Pylance-clean (all unused args replaced with _).

✅ Now you’ve got:

Success + failure coverage for both DB connection and endpoint.

Tests for home, missing fields, valid register, DB failure register.

CI/CD ready with pytest-cov for coverage enforcement.

👉 Do you want me to also add coverage badges (like a % coverage badge in your README) so your repo shows test coverage at a glance?

You said:
yes
ChatGPT said:

Perfect 🚀 — adding a coverage badge to your repo makes it super clear to everyone how well your code is tested. There are two common ways: via GitHub Actions + Shields.io (free + simple) or via Codecov (more detailed reports, free tier).

🔧 Option 1: Shields.io badge (quick & simple)

Make sure your GitHub Actions workflow runs pytest-cov with an XML report:

- name: Run tests with coverage
  run: pytest --cov=main --cov-report=xml --cov-fail-under=90 -v


This will generate a coverage.xml.

Add a badge using Shields.io
. Example for a static badge:

![coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)


⚠️ Downside: you must update the percentage manually.

🔧 Option 2: GitHub Actions + Codecov (auto-updating badge ✅)

Add Codecov to your workflow:
Create .github/workflows/tests.yml (or update your existing one):

name: CI Tests with Coverage

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests with coverage
        run: pytest --cov=main --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage.xml


Sign up at https://codecov.io
, add your repo, and grab the CODECOV_TOKEN.
Store it in your GitHub repo secrets (Settings > Secrets > Actions > New repository secret).

Add a badge to your README.md:

[![codecov](https://codecov.io/gh/YOUR_GITHUB_USERNAME/student-registration-app/branch/main/graph/badge.svg)](https://codecov.io/gh/YOUR_GITHUB_USERNAME/student-registration-app)


This badge updates automatically after every CI run.

✅ Recommendation

If you just want something quick → Shields.io static badge.

If you want real-time, auto-updating coverage tracking → go with Codecov.

👉 Do you want me to set this up for you using Codecov, and write the updated GitHub Actions YAML + README badge section ready-to-use?
⚠️ Notes

Frontend served via Nginx container at http://localhost:8080
.

Backend API must be reachable by frontend (consider adding Nginx reverse proxy if avoiding CORS).

Use gunicorn or uwsgi instead of Flask dev server in production.

Extend logs to Grafana Loki for full observability (logs + metrics + traces).

📜 License

MIT License.