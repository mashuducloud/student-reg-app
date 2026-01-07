# db.py
import logging
from contextlib import contextmanager

import mysql.connector
from config import DB_CONFIG
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


def create_db_connection():
    """
    Low-level DB connection helper with tracing & logging.
    """
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
                    extra={
                        "db.host": DB_CONFIG["host"],
                        "db.name": DB_CONFIG["database"],
                    },
                )
            else:
                span.set_status(Status(StatusCode.ERROR, "DB connection not active"))
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            log.error(f"Database connection failed: {e}", extra={"db.error": str(e)})
            connection = None
    return connection


@contextmanager
def get_connection():
    """
    Context manager for DB connections so callers don't forget to close.
    """
    conn = create_db_connection()
    try:
        yield conn
    finally:
        if conn and conn.is_connected():
            conn.close()
