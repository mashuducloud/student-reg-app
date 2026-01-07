# main.py
import logging
import os

from auth import requires_auth
from db import create_db_connection
from flask import Flask, jsonify, request
from flask_cors import CORS
from opentelemetry import metrics, trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, ConsoleLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode, get_current_span

# 🔹 NEW: Assessments repository imports
from repositories.assessments_repository import (
    create_assessment,
    delete_assessment,
    get_assessment,
    list_assessments,
    update_assessment,
)
from repositories.attendance_repository import (
    create_attendance,
    delete_attendance,
    get_attendance,
    list_attendance,
    list_attendance_for_student,
    update_attendance,
)
from repositories.documents_repository import (
    create_document,
    delete_document,
    get_document,
    list_documents,
    list_documents_for_student,
)
from repositories.enrolments_repository import (
    create_enrolment,
    delete_enrolment,
    get_enrolment,
    list_enrolments,
    update_enrolment,
)
from repositories.programmes_repository import (
    ProgrammeCodeAlreadyExistsError,
    create_programme,
    delete_programme,
    get_programme,
    list_programmes,
    update_programme,
)
from repositories.stipends_repository import (
    create_stipend,
    delete_stipend,
    get_stipend,
    list_stipends,
    list_stipends_for_student,
    update_stipend,
)
from repositories.students_repository import (
    EmailAlreadyExistsError,
    delete_student,
    get_student,
    list_students,
    register_student,
    update_student,
)
from repositories.workplace_placements_repository import (
    create_placement,
    delete_placement,
    get_placement,
    list_placements,
    update_placement,
)

# =============================================================================
# Environment-driven config
# =============================================================================

SERVICE_NAME = os.getenv("SERVICE_NAME", "student-registration-service")

OTEL_EXPORTER_OTLP_ENDPOINT = os.getenv(
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "http://otel-collector:4318",
).strip()

ENABLE_CONSOLE_SPANS = os.getenv("ENABLE_CONSOLE_SPANS", "false").lower() == "true"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENABLE_CONSOLE_LOG_EXPORTER = os.getenv("ENABLE_CONSOLE_LOG_EXPORTER", "true").lower() == "true"

ENABLE_OTLP_LOG_EXPORTER = os.getenv("ENABLE_OTLP_LOG_EXPORTER", "false").lower() == "true"

ENABLE_PROMETHEUS = os.getenv("ENABLE_PROMETHEUS", "true").lower() == "true"
PROMETHEUS_PORT = int(os.getenv("PROMETHEUS_PORT", "9100"))
PROMETHEUS_HOST = os.getenv("PROMETHEUS_HOST", "0.0.0.0")

FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))

# =============================================================================
# Base logging config (Python stdlib)
# =============================================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

log = logging.getLogger(__name__)

# =============================================================================
# Resource & Tracing Access
# =============================================================================

resource = Resource(attributes={"service.name": SERVICE_NAME})
tracer = trace.get_tracer(__name__)

# =============================================================================
# Logging Setup (OTel logging + Python logging bridge)
# =============================================================================

logger_provider = LoggerProvider(resource=resource)
set_logger_provider(logger_provider)

if ENABLE_CONSOLE_LOG_EXPORTER:
    console_exporter = ConsoleLogExporter()
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(console_exporter))

root_logger = logging.getLogger()
if not any(isinstance(h, LoggingHandler) for h in root_logger.handlers):
    otel_handler = LoggingHandler(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        logger_provider=logger_provider,
    )
    root_logger.addHandler(otel_handler)

log = logging.getLogger(__name__)

# =============================================================================
# Metrics Setup
# =============================================================================

meter = metrics.get_meter("student-registration-metrics", "0.1.0")

request_counter = meter.create_counter(
    name="student_registration_requests_total",
    unit="1",
    description="Counts incoming student registration requests",
)

# --- Flask App ---
app = Flask(__name__)
CORS(app)


@app.before_request
def count_requests():
    request_counter.add(
        1,
        {
            "http_method": request.method,
            "http_route": request.path,
        },
    )


# --- Endpoints ---


@app.route("/")
def home():
    span = get_current_span()
    span.set_status(Status(StatusCode.OK))
    span.set_attribute("endpoint", "home")
    return "Student Registration API is running 🚀"


@app.route("/health", methods=["GET"])
def health():
    span = get_current_span()
    span.update_name("health_handler")

    try:
        connection = create_db_connection()
        if connection and connection.is_connected():
            connection.close()
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("health.db_status", "ok")
            return jsonify({"status": "healthy"}), 200
        else:
            span.set_status(Status(StatusCode.ERROR, "DB not connected"))
            span.set_attribute("health.db_status", "down")
            return (
                jsonify({"status": "unhealthy", "reason": "DB not connected"}),
                500,
            )
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        span.set_attribute("health.db_status", "error")
        return jsonify({"status": "unhealthy", "reason": str(e)}), 500


# -------- CREATE (legacy alias) --------
@app.route("/register", methods=["POST"])
@requires_auth
def register_student_legacy():
    span = get_current_span()
    data = request.get_json(silent=True)
    span.add_event("request.body_parsed")

    if data:
        span.set_attribute("student.first_name", data.get("first_name", ""))
        span.set_attribute("student.last_name", data.get("last_name", ""))
        span.set_attribute("student.email", data.get("email", ""))

    if not data:
        msg = "Invalid request body"
        span.set_status(Status(StatusCode.ERROR, msg))
        span.add_event("validation_failed", {"reason": msg})
        return jsonify({"error": "Invalid request"}), 400

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    if not all([first_name, last_name, email]):
        msg = "Missing required fields"
        span.set_status(Status(StatusCode.ERROR, msg))
        span.add_event("validation_failed", {"reason": msg})
        return jsonify(
            {"error": "first_name, last_name, and email required"},
        ), 400

    try:
        student_id = register_student(first_name, last_name, email)

        if student_id is not None:
            span.set_attribute("student.id", student_id)
            span.add_event(
                "student_registered",
                {"student.id": student_id, "student.email": email},
            )
            log.info(
                "Student registered successfully (legacy endpoint)",
                extra={**data, "student.id": student_id},
            )
            return (
                jsonify(
                    {
                        "message": "Student registered successfully",
                        "id": student_id,
                    }
                ),
                201,
            )
        else:
            span.add_event(
                "student_registered",
                {"student.id": "unknown", "student.email": email},
            )
            log.info(
                "Student registered successfully (no student_id available)",
                extra=data,
            )
            return jsonify({"message": "Student registered successfully"}), 201

    except EmailAlreadyExistsError as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, "duplicate_email"))
        span.add_event("student_registration_failed", {"reason": "duplicate_email"})
        log.warning(
            "Registration failed: duplicate email",
            extra={"email": email, "error": str(e)},
        )
        return jsonify({"error": "Email already exists"}), 409

    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        span.add_event(
            "student_registration_failed",
            {"error": str(e)},
        )
        log.error(f"Registration failed: {e}", extra={"error": str(e)})
        return jsonify({"error": "Failed to register student"}), 500


# ===============================
#   RESTful Students CRUD API
# ===============================


# CREATE
@app.route("/students", methods=["POST"])
@requires_auth
def create_student():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    if not all([first_name, last_name, email]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "first_name, last_name, and email required"},
        ), 400

    try:
        student_id = register_student(first_name, last_name, email)
        span.set_attribute("student.id", student_id)
        return jsonify(
            {
                "message": "Student created",
                "student": {
                    "id": student_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                },
            }
        ), 201

    except EmailAlreadyExistsError as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, "duplicate_email"))
        log.warning(
            "Create student failed: duplicate email",
            extra={"email": email, "error": str(e)},
        )
        return jsonify({"error": "Email already exists"}), 409

    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create student"}), 500


# READ ALL
@app.route("/students", methods=["GET"])
@requires_auth
def get_students():
    span = get_current_span()
    try:
        students = list_students()
        span.set_attribute("students.count", len(students))
        span.set_status(Status(StatusCode.OK))
        return jsonify(students), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch students"}), 500


# READ ONE
@app.route("/students/<int:student_id>", methods=["GET"])
@requires_auth
def get_student_by_id(student_id: int):
    span = get_current_span()
    span.set_attribute("student.id", student_id)
    try:
        student = get_student(student_id)
        if not student:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Student not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(student), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch student"}), 500


# UPDATE
@app.route("/students/<int:student_id>", methods=["PUT"])
@requires_auth
def update_student_by_id(student_id: int):
    span = get_current_span()
    span.set_attribute("student.id", student_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    email = data.get("email")

    if not all([first_name, last_name, email]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "first_name, last_name, and email required"},
        ), 400

    try:
        updated = update_student(student_id, first_name, last_name, email)
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Student not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Student updated", "student": updated}), 200

    except EmailAlreadyExistsError as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, "duplicate_email"))
        log.warning(
            "Update student failed: duplicate email",
            extra={"student.id": student_id, "email": email, "error": str(e)},
        )
        return jsonify({"error": "Email already exists"}), 409

    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update student"}), 500


# DELETE
@app.route("/students/<int:student_id>", methods=["DELETE"])
@requires_auth
def delete_student_by_id(student_id: int):
    span = get_current_span()
    span.set_attribute("student.id", student_id)

    try:
        deleted = delete_student(student_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Student not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Student deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete student"}), 500


# =========================================
#   Programmes API (with description)
# =========================================


@app.route("/programmes", methods=["GET"])
@requires_auth
def api_list_programmes():
    span = get_current_span()
    try:
        programmes = list_programmes()
        span.set_attribute("programmes.count", len(programmes))
        span.set_status(Status(StatusCode.OK))
        return jsonify(programmes), 200
    except Exception as e:
        app.logger.exception("Error fetching programmes")
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": f"Failed to fetch programmes: {e}"}), 500


@app.route("/programmes", methods=["POST"])
@requires_auth
def api_create_programme():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    programme_name = data.get("programme_name")
    programme_code = data.get("programme_code")
    nqf_level = data.get("nqf_level")
    credits = data.get("credits")
    description = data.get("description")

    if not all([programme_name, programme_code]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "programme_name and programme_code required"},
        ), 400

    try:
        pid = create_programme(
            programme_name=programme_name,
            programme_code=programme_code,
            nqf_level=nqf_level,
            credits=credits,
            description=description,
        )
        programme = get_programme(pid)
        span.set_attribute("programme.id", pid)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Programme created", "programme": programme}), 201
    except ProgrammeCodeAlreadyExistsError as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, "duplicate_programme_code"))
        return jsonify({"error": "Programme code already exists"}), 409
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create programme"}), 500


@app.route("/programmes/<int:programme_id>", methods=["GET"])
@requires_auth
def api_get_programme(programme_id: int):
    span = get_current_span()
    span.set_attribute("programme.id", programme_id)
    try:
        programme = get_programme(programme_id)
        if not programme:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Programme not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(programme), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch programme"}), 500


@app.route("/programmes/<int:programme_id>", methods=["PUT"])
@requires_auth
def api_update_programme(programme_id: int):
    span = get_current_span()
    span.set_attribute("programme.id", programme_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    programme_name = data.get("programme_name")
    programme_code = data.get("programme_code")
    nqf_level = data.get("nqf_level")
    credits = data.get("credits")
    description = data.get("description")

    if not all([programme_name, programme_code]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "programme_name and programme_code required"},
        ), 400

    try:
        updated = update_programme(
            programme_id=programme_id,
            programme_name=programme_name,
            programme_code=programme_code,
            nqf_level=nqf_level,
            credits=credits,
            description=description,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Programme not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Programme updated", "programme": updated}), 200
    except ProgrammeCodeAlreadyExistsError as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, "duplicate_programme_code"))
        return jsonify({"error": "Programme code already exists"}), 409
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update programme"}), 500


@app.route("/programmes/<int:programme_id>", methods=["DELETE"])
@requires_auth
def api_delete_programme(programme_id: int):
    span = get_current_span()
    span.set_attribute("programme.id", programme_id)

    try:
        deleted = delete_programme(programme_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Programme not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Programme deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete programme"}), 500


# =========================================
#   Enrolments API
# =========================================


@app.route("/enrolments", methods=["GET"])
@requires_auth
def api_list_enrolments():
    span = get_current_span()
    try:
        enrolments = list_enrolments()
        span.set_attribute("enrolments.count", len(enrolments))
        span.set_status(Status(StatusCode.OK))
        return jsonify(enrolments), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch enrolments"}), 500


@app.route("/enrolments", methods=["POST"])
@requires_auth
def api_create_enrolment():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    programme_id = data.get("programme_id")
    enrolment_status = data.get("enrolment_status", "applied")
    enrolment_date = data.get("enrolment_date")
    completion_date = data.get("completion_date")

    if not all([student_id, programme_id]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id and programme_id required"},
        ), 400

    try:
        eid = create_enrolment(
            student_id=int(student_id),
            programme_id=int(programme_id),
            enrolment_status=enrolment_status,
            enrolment_date=enrolment_date,
            completion_date=completion_date,
        )
        enrolment = get_enrolment(eid)
        span.set_attribute("enrolment.id", eid)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Enrolment created", "enrolment": enrolment}), 201
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create enrolment"}), 500


@app.route("/enrolments/<int:enrolment_id>", methods=["GET"])
@requires_auth
def api_get_enrolment(enrolment_id: int):
    span = get_current_span()
    span.set_attribute("enrolment.id", enrolment_id)

    try:
        enrolment = get_enrolment(enrolment_id)
        if not enrolment:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Enrolment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(enrolment), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch enrolment"}), 500


@app.route("/enrolments/<int:enrolment_id>", methods=["PUT"])
@requires_auth
def api_update_enrolment(enrolment_id: int):
    span = get_current_span()
    span.set_attribute("enrolment.id", enrolment_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    programme_id = data.get("programme_id")
    enrolment_status = data.get("enrolment_status")
    enrolment_date = data.get("enrolment_date")
    completion_date = data.get("completion_date")

    if not all([student_id, programme_id, enrolment_status]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, programme_id and enrolment_status required"},
        ), 400

    try:
        updated = update_enrolment(
            enrolment_id=enrolment_id,
            student_id=int(student_id),
            programme_id=int(programme_id),
            enrolment_status=enrolment_status,
            enrolment_date=enrolment_date,
            completion_date=completion_date,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Enrolment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Enrolment updated", "enrolment": updated}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update enrolment"}), 500


@app.route("/enrolments/<int:enrolment_id>", methods=["DELETE"])
@requires_auth
def api_delete_enrolment(enrolment_id: int):
    span = get_current_span()
    span.set_attribute("enrolment.id", enrolment_id)

    try:
        deleted = delete_enrolment(enrolment_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Enrolment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Enrolment deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete enrolment"}), 500


# =========================================
#   Workplace Placements API
# =========================================


@app.route("/workplace-placements", methods=["GET"])
@requires_auth
def api_list_placements():
    span = get_current_span()
    try:
        placements = list_placements()
        span.set_attribute("placements.count", len(placements))
        span.set_status(Status(StatusCode.OK))
        return jsonify(placements), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch placements"}), 500


@app.route("/workplace-placements", methods=["POST"])
@requires_auth
def api_create_placement():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    employer_name = data.get("employer_name")
    employer_contact = data.get("employer_contact")
    supervisor_name = data.get("supervisor_name")
    supervisor_phone = data.get("supervisor_phone")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([student_id, employer_name]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id and employer_name required"},
        ), 400

    try:
        pid = create_placement(
            student_id=int(student_id),
            employer_name=employer_name,
            employer_contact=employer_contact,
            supervisor_name=supervisor_name,
            supervisor_phone=supervisor_phone,
            start_date=start_date,
            end_date=end_date,
        )
        placement = get_placement(pid)
        span.set_attribute("placement.id", pid)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Placement created", "placement": placement}), 201
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create placement"}), 500


@app.route("/workplace-placements/<int:placement_id>", methods=["GET"])
@requires_auth
def api_get_placement(placement_id: int):
    span = get_current_span()
    span.set_attribute("placement.id", placement_id)

    try:
        placement = get_placement(placement_id)
        if not placement:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Placement not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(placement), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch placement"}), 500


@app.route("/workplace-placements/<int:placement_id>", methods=["PUT"])
@requires_auth
def api_update_placement(placement_id: int):
    span = get_current_span()
    span.set_attribute("placement.id", placement_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    employer_name = data.get("employer_name")
    employer_contact = data.get("employer_contact")
    supervisor_name = data.get("supervisor_name")
    supervisor_phone = data.get("supervisor_phone")
    start_date = data.get("start_date")
    end_date = data.get("end_date")

    if not all([student_id, employer_name]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id and employer_name required"},
        ), 400

    try:
        updated = update_placement(
            placement_id=placement_id,
            student_id=int(student_id),
            employer_name=employer_name,
            employer_contact=employer_contact,
            supervisor_name=supervisor_name,
            supervisor_phone=supervisor_phone,
            start_date=start_date,
            end_date=end_date,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Placement not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Placement updated", "placement": updated}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update placement"}), 500


@app.route("/workplace-placements/<int:placement_id>", methods=["DELETE"])
@requires_auth
def api_delete_placement(placement_id: int):
    span = get_current_span()
    span.set_attribute("placement.id", placement_id)

    try:
        deleted = delete_placement(placement_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Placement not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Placement deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete placement"}), 500


# =========================================
#   Attendance API
# =========================================


@app.route("/attendance", methods=["GET"])
@requires_auth
def api_list_attendance():
    span = get_current_span()
    student_id = request.args.get("student_id")

    try:
        if student_id:
            records = list_attendance_for_student(int(student_id))
        else:
            records = list_attendance()

        span.set_attribute("attendance.count", len(records))
        span.set_status(Status(StatusCode.OK))
        return jsonify(records), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch attendance"}), 500


@app.route("/attendance", methods=["POST"])
@requires_auth
def api_create_attendance():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    attendance_date = data.get("attendance_date")
    status = data.get("status", "present")

    if not all([student_id, attendance_date]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id and attendance_date required"},
        ), 400

    try:
        aid = create_attendance(
            student_id=int(student_id),
            attendance_date=attendance_date,
            status=status,
        )
        record = get_attendance(aid)
        span.set_attribute("attendance.id", aid)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Attendance created", "attendance": record}), 201
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create attendance"}), 500


@app.route("/attendance/<int:attendance_id>", methods=["GET"])
@requires_auth
def api_get_attendance(attendance_id: int):
    span = get_current_span()
    span.set_attribute("attendance.id", attendance_id)

    try:
        record = get_attendance(attendance_id)
        if not record:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Attendance not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(record), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch attendance"}), 500


@app.route("/attendance/<int:attendance_id>", methods=["PUT"])
@requires_auth
def api_update_attendance(attendance_id: int):
    span = get_current_span()
    span.set_attribute("attendance.id", attendance_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    attendance_date = data.get("attendance_date")
    status = data.get("status")

    if not all([student_id, attendance_date, status]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, attendance_date and status required"},
        ), 400

    try:
        updated = update_attendance(
            attendance_id=attendance_id,
            student_id=int(student_id),
            attendance_date=attendance_date,
            status=status,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Attendance not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Attendance updated", "attendance": updated}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update attendance"}), 500


@app.route("/attendance/<int:attendance_id>", methods=["DELETE"])
@requires_auth
def api_delete_attendance(attendance_id: int):
    span = get_current_span()
    span.set_attribute("attendance.id", attendance_id)

    try:
        deleted = delete_attendance(attendance_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Attendance not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Attendance deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete attendance"}), 500


# =========================================
#   Stipends API
# =========================================


@app.route("/stipends", methods=["GET"])
@requires_auth
def api_list_stipends():
    span = get_current_span()
    student_id = request.args.get("student_id")

    try:
        if student_id:
            records = list_stipends_for_student(int(student_id))
        else:
            records = list_stipends()

        span.set_attribute("stipends.count", len(records))
        span.set_status(Status(StatusCode.OK))
        return jsonify(records), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch stipends"}), 500


@app.route("/stipends", methods=["POST"])
@requires_auth
def api_create_stipend():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    month = data.get("month")  # 'YYYY-MM'
    amount = data.get("amount")
    status = data.get("status", "submitted")

    if not all([student_id, month, amount is not None]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, month and amount required"},
        ), 400

    try:
        sid = create_stipend(
            student_id=int(student_id),
            month=month,
            amount=float(amount),
            status=status,
        )
        record = get_stipend(sid)
        span.set_attribute("stipend.id", sid)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Stipend created", "stipend": record}), 201
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create stipend"}), 500


@app.route("/stipends/<int:stipend_id>", methods=["GET"])
@requires_auth
def api_get_stipend(stipend_id: int):
    span = get_current_span()
    span.set_attribute("stipend.id", stipend_id)

    try:
        record = get_stipend(stipend_id)
        if not record:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Stipend not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(record), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch stipend"}), 500


@app.route("/stipends/<int:stipend_id>", methods=["PUT"])
@requires_auth
def api_update_stipend(stipend_id: int):
    span = get_current_span()
    span.set_attribute("stipend.id", stipend_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    month = data.get("month")
    amount = data.get("amount")
    status = data.get("status")

    if not all([student_id, month, amount is not None, status]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, month, amount and status required"},
        ), 400

    try:
        updated = update_stipend(
            stipend_id=stipend_id,
            student_id=int(student_id),
            month=month,
            amount=float(amount),
            status=status,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Stipend not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Stipend updated", "stipend": updated}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update stipend"}), 500


@app.route("/stipends/<int:stipend_id>", methods=["DELETE"])
@requires_auth
def api_delete_stipend(stipend_id: int):
    span = get_current_span()
    span.set_attribute("stipend.id", stipend_id)

    try:
        deleted = delete_stipend(stipend_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Stipend not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Stipend deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete stipend"}), 500


# =========================================
#   Assessments API
# =========================================


@app.route("/assessments", methods=["GET"])
@requires_auth
def api_list_assessments():
    span = get_current_span()
    try:
        assessments = list_assessments()
        span.set_attribute("assessments.count", len(assessments))
        span.set_status(Status(StatusCode.OK))
        return jsonify(assessments), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch assessments"}), 500


@app.route("/assessments", methods=["POST"])
@requires_auth
def api_create_assessment():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    programme_id = data.get("programme_id")
    assessment_type = data.get("assessment_type")
    assessment_name = data.get("assessment_name")
    assessment_date = data.get("assessment_date")
    score = data.get("score")
    max_score = data.get("max_score")
    result = data.get("result")
    moderation_outcome = data.get("moderation_outcome")

    # minimal required fields; adjust if you like
    if not all([student_id, programme_id, assessment_type, assessment_name]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, programme_id, assessment_type and assessment_name required"},
        ), 400

    try:
        aid = create_assessment(
            student_id=int(student_id),
            programme_id=int(programme_id),
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            assessment_date=assessment_date,
            score=score,
            max_score=max_score,
            result=result,
            moderation_outcome=moderation_outcome,
        )
        assessment = get_assessment(aid)
        span.set_attribute("assessment.id", aid)
        span.set_status(Status(StatusCode.OK))
        return (
            jsonify({"message": "Assessment created", "assessment": assessment}),
            201,
        )
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create assessment"}), 500


@app.route("/assessments/<int:assessment_id>", methods=["GET"])
@requires_auth
def api_get_assessment(assessment_id: int):
    span = get_current_span()
    span.set_attribute("assessment.id", assessment_id)

    try:
        assessment = get_assessment(assessment_id)
        if not assessment:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Assessment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(assessment), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch assessment"}), 500


@app.route("/assessments/<int:assessment_id>", methods=["PUT"])
@requires_auth
def api_update_assessment(assessment_id: int):
    span = get_current_span()
    span.set_attribute("assessment.id", assessment_id)
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    programme_id = data.get("programme_id")
    assessment_type = data.get("assessment_type")
    assessment_name = data.get("assessment_name")
    assessment_date = data.get("assessment_date")
    score = data.get("score")
    max_score = data.get("max_score")
    result = data.get("result")
    moderation_outcome = data.get("moderation_outcome")

    if not all([student_id, programme_id, assessment_type, assessment_name]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, programme_id, assessment_type and assessment_name required"},
        ), 400

    try:
        updated = update_assessment(
            assessment_id=assessment_id,
            student_id=int(student_id),
            programme_id=int(programme_id),
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            assessment_date=assessment_date,
            score=score,
            max_score=max_score,
            result=result,
            moderation_outcome=moderation_outcome,
        )
        if not updated:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Assessment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Assessment updated", "assessment": updated}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to update assessment"}), 500


@app.route("/assessments/<int:assessment_id>", methods=["DELETE"])
@requires_auth
def api_delete_assessment(assessment_id: int):
    span = get_current_span()
    span.set_attribute("assessment.id", assessment_id)

    try:
        deleted = delete_assessment(assessment_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Assessment not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Assessment deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete assessment"}), 500


# =========================================
#   Documents API
# =========================================


@app.route("/documents", methods=["GET"])
@requires_auth
def api_list_documents():
    span = get_current_span()
    student_id = request.args.get("student_id")

    try:
        if student_id:
            docs = list_documents_for_student(int(student_id))
        else:
            docs = list_documents()

        span.set_attribute("documents.count", len(docs))
        span.set_status(Status(StatusCode.OK))
        return jsonify(docs), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch documents"}), 500


@app.route("/documents", methods=["POST"])
@requires_auth
def api_create_document():
    span = get_current_span()
    data = request.get_json(silent=True)

    if not data:
        span.set_status(Status(StatusCode.ERROR, "Invalid request body"))
        return jsonify({"error": "Invalid request"}), 400

    student_id = data.get("student_id")
    document_name = data.get("document_name")
    file_path = data.get("file_path")
    document_type = data.get("document_type")
    uploaded_by = data.get("uploaded_by")

    if not all([student_id, document_name, file_path]):
        span.set_status(Status(StatusCode.ERROR, "Missing required fields"))
        return jsonify(
            {"error": "student_id, document_name and file_path required"},
        ), 400

    try:
        did = create_document(
            student_id=int(student_id),
            document_name=document_name,
            file_path=file_path,
            document_type=document_type,
            uploaded_by=uploaded_by,
        )
        doc = get_document(did)
        span.set_attribute("document.id", did)
        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Document created", "document": doc}), 201
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to create document"}), 500


@app.route("/documents/<int:document_id>", methods=["GET"])
@requires_auth
def api_get_document(document_id: int):
    span = get_current_span()
    span.set_attribute("document.id", document_id)

    try:
        doc = get_document(document_id)
        if not doc:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Document not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify(doc), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to fetch document"}), 500


@app.route("/documents/<int:document_id>", methods=["DELETE"])
@requires_auth
def api_delete_document(document_id: int):
    span = get_current_span()
    span.set_attribute("document.id", document_id)

    try:
        deleted = delete_document(document_id)
        if not deleted:
            span.set_status(Status(StatusCode.OK))
            return jsonify({"error": "Document not found"}), 404

        span.set_status(Status(StatusCode.OK))
        return jsonify({"message": "Document deleted"}), 200
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR, str(e)))
        return jsonify({"error": "Failed to delete document"}), 500


# --- Run Flask App ---
if __name__ == "__main__":
    app.run(
        debug=FLASK_DEBUG,
        host=FLASK_HOST,
        port=FLASK_PORT,
        use_reloader=FLASK_DEBUG,
    )
