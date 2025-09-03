import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import logging

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
    'user': 'root',  # <-- Replace with your user
    'password': 'Barcelona@1819'  # <-- Replace with your password)
}
# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- Database Connection Function ---
def create_db_connection():
    """Establishes a connection to the MySQL database."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            log.info("✅ Successfully connected to the database", extra={"db.host": DB_CONFIG["host"], "db.name": DB_CONFIG["database"]})
    except Error as e:
        log.error(f"Database connection failed: {e}", extra={"db.error": str(e)})
    return connection

# --- API Endpoint for Student Registration ---
@app.route('/register', methods=['POST'])
def register_student():
    with tracer.start_as_current_span("register_student_request") as span:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid request"}), 400

        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')

        if not all([first_name, last_name, email]):
            return jsonify({"error": "first_name, last_name, and email are required"}), 400

        try:
            connection = create_db_connection()
            if connection is None:
                raise Exception("Failed to connect to database")

            cursor = connection.cursor()
            insert_query = """
                INSERT INTO students (first_name, last_name, email)
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (first_name, last_name, email))
            connection.commit()
            cursor.close()
            connection.close()

            log.info("Student registered successfully", extra=data)
            span.set_status(Status(StatusCode.OK))
            return jsonify({"message": "Student registered successfully"}), 201

        except Exception as e:
            log.error(f"Error during student registration: {e}", extra={"error": str(e)})
            span.set_status(Status(StatusCode.ERROR, str(e)))
            return jsonify({"error": "Failed to register student"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


 
