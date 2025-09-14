import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

# --- OpenTelemetry Imports ---
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider   # ✅ FIXED
from prometheus_client import start_http_server

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.trace import Status, StatusCode

# --- Resource & Tracing Setup ---
resource = Resource(attributes={"service.name": "student-registration-service"})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)

# --- OTLP Exporter (to otel-collector in Docker network) ---
grpc_exporter = OTLPGrpcExporter(
    endpoint="otel-collector:4317",
    insecure=True
)

# Add span processors
provider = trace.get_tracer_provider()
provider.add_span_processor(BatchSpanProcessor(grpc_exporter))
provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

# --- Logging Setup ---
logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogExporter()))
handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
log = logging.getLogger(__name__)

# --- Metrics Setup ---
prometheus_reader = PrometheusMetricReader()
metrics.set_meter_provider(
    MeterProvider(resource=resource, metric_readers=[prometheus_reader])
)
meter = metrics.get_meter(__name__)

# Request counter metric
request_counter = meter.create_counter(
    name="student_registration_requests_total",
    description="Counts incoming student registration requests"
)

# Start Prometheus metrics server
start_http_server(9100)

# --- Flask App ---
app = Flask(__name__)
CORS(app)



# --- Middleware for tracing ---
@app.before_request
def start_request_span():
    request.start_time = time.time()
    request_counter.add(1)
    request.span = tracer.start_span(f"HTTP {request.method} {request.path}")
    request.span.set_attribute("http.method", request.method)
    request.span.set_attribute("http.url", request.url)

@app.after_request
def end_request_span(response):
    if hasattr(request, "span") and request.span is not None:
        duration = time.time() - request.start_time
        request.span.set_attribute("http.status_code", response.status_code)
        request.span.set_attribute("http.duration_ms", int(duration * 1000))
        if response.status_code >= 400:
            request.span.set_status(Status(StatusCode.ERROR))
        else:
            request.span.set_status(Status(StatusCode.OK))
        request.span.end()
        request.span = None
    return response

@app.teardown_request
def teardown_request_span(error=None):
    if hasattr(request, "span") and request.span is not None:
        duration = time.time() - request.start_time
        request.span.set_attribute("http.duration_ms", int(duration * 1000))
        if error:
            request.span.record_exception(error)
            request.span.set_status(Status(StatusCode.ERROR, str(error)))
        request.span.end()
        request.span = None

# --- Database Connection ---
def create_db_connection():
    connection = None
    with tracer.start_as_current_span("create_db_connection") as span:
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                span.set_status(Status(StatusCode.OK))
                span.set_attribute("db.system", "mysql")
                span.set_attribute("db.user", DB_CONFIG["user"])
                span.set_attribute("db.name", DB_CONFIG["database"])
                span.set_attribute("net.peer.name", DB_CONFIG["host"])
                log.info(
                    "Connected to DB",
                    extra={"db.host": DB_CONFIG["host"], "db.name": DB_CONFIG["database"]}
                )
        except Exception as e:  # 👈 catch ALL exceptions
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error(f"Database connection failed: {e}", extra={"db.error": str(e)})
            connection = None   # 👈 ensure None is returned on failure
    return connection


# --- Endpoints ---
@app.route("/")
def home():
    with tracer.start_as_current_span("home_handler") as span:
        span.set_status(Status(StatusCode.OK))
        return "Student Registration API is running 🚀"

@app.route("/register", methods=["POST"])
def register_student():
    with tracer.start_as_current_span("register_student_handler") as span:
        data = request.get_json(silent=True)
        span.set_attribute("request.body", str(data))

        if not data:
            span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
            return jsonify({"error": "Invalid request"}), 400

        first_name = data.get("first_name")
        last_name = data.get("last_name")
        email = data.get("email")

        if not all([first_name, last_name, email]):
            span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
            return jsonify({"error": "first_name, last_name, and email required"}), 400

        try:
            connection = create_db_connection()
            if connection is None:
                raise Exception("DB connection failed")

            with tracer.start_as_current_span("db_insert_student") as db_span:
                db_span.set_attribute("db.statement", "INSERT INTO students (first_name, last_name, email) VALUES (?, ?, ?)")
                cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO students (first_name, last_name, email) VALUES (%s, %s, %s)",
                    (first_name, last_name, email)
                )
                connection.commit()
                cursor.close()
                connection.close()
                db_span.set_status(Status(StatusCode.OK))

            log.info("Student registered successfully", extra=data)
            span.set_status(Status(StatusCode.OK))
            return jsonify({"message": "Student registered successfully"}), 201

        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error(f"Registration failed: {e}", extra={"error": str(e)})
            return jsonify({"error": "Failed to register student"}), 500

# --- Run Flask App ---
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000, use_reloader=False) 