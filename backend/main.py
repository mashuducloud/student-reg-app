import os
import time
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

# --- OpenTelemetry Imports ---
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode

from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter

# --- OpenTelemetry Initialization ---
resource = Resource(attributes={
    "service.name": "student-registration-service"
})

trace.set_tracer_provider(TracerProvider(resource=resource))
tracer = trace.get_tracer(__name__)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(ConsoleLogExporter()))

handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)
logging.getLogger().addHandler(handler)
log = logging.getLogger(__name__)

# --- Configuration ---
DB_CONFIG = {
    'host': 'localhost',
    'database': 'student_registration_db',
    'user': 'root',  
    'password': 'Barcelona@1819'  
}

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Middleware for Request Tracing ---
@app.before_request
def start_request_span():
    request.start_time = time.time()
    request.span = tracer.start_span(
        name=f"HTTP {request.method} {request.path}"
    )
    request.span.set_attribute("http.method", request.method)
    request.span.set_attribute("http.url", request.url)


@app.after_request
def end_request_span(response):
    if hasattr(request, "span"):
        duration = time.time() - request.start_time
        request.span.set_attribute("http.status_code", response.status_code)
        request.span.set_attribute("http.duration_ms", int(duration * 1000))
        if response.status_code >= 400:
            request.span.set_status(Status(StatusCode.ERROR))
        request.span.end()
        request.span = None
    return response


@app.teardown_request
def teardown_request_span(error=None):
    """Guarantee span closure even if an exception occurs."""
    if hasattr(request, "span") and request.span is not None:
        duration = time.time() - request.start_time
        request.span.set_attribute("http.duration_ms", int(duration * 1000))

        if error:
            request.span.record_exception(error)
            request.span.set_status(Status(StatusCode.ERROR, str(error)))
        else:
            request.span.set_status(Status(StatusCode.OK))

        request.span.end()
        request.span = None


# --- Database Connection Function ---
def create_db_connection():
    """Establishes a connection to the MySQL database."""
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
                    "Successfully connected to the database",
                    extra={"db.host": DB_CONFIG["host"], "db.name": DB_CONFIG["database"]}
                )
        except Error as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error(f"Database connection failed: {e}", extra={"db.error": str(e)})
    return connection


# --- Health Check Endpoint ---
@app.route("/")
def home():
    with tracer.start_as_current_span("home_handler") as span:
        span.set_attribute("endpoint", "/")
        span.set_attribute("http.method", request.method)
        span.set_status(Status(StatusCode.OK))
        return "Student Registration API is running 🚀"


# --- API Endpoint for Student Registration ---
@app.route('/register', methods=['POST'])
def register_student():
    with tracer.start_as_current_span("register_student_handler") as span:
        data = request.get_json(silent=True)
        span.set_attribute("request.body", str(data))

        if not data:
            span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
            return jsonify({"error": "Invalid request"}), 400

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')

        if not all([first_name, last_name, email]):
            span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
            return jsonify({"error": "first_name, last_name, and email are required"}), 400

        try:
            connection = create_db_connection()
            if connection is None:
                raise Exception("Failed to connect to database")

            with tracer.start_as_current_span("db_insert_student") as db_span:
                db_span.set_attribute(
                    "db.statement",
                    "INSERT INTO students (first_name, last_name, email) VALUES (?, ?, ?)"
                )
                cursor = connection.cursor()
                insert_query = """
                    INSERT INTO students (first_name, last_name, email)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_query, (first_name, last_name, email))
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
            log.error(f"Error during student registration: {e}", extra={"error": str(e)})
            return jsonify({"error": "Failed to register student"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)