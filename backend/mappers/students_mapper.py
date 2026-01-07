# mappers/students_mapper.py
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class DuplicateEmailError(Exception):
    """Raised when a UNIQUE(email) constraint is violated."""

    pass


@dataclass
class Student:
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    registration_date: Optional[datetime] = None

    def as_insert_tuple(self) -> tuple[str, str, str]:
        return (self.first_name, self.last_name, self.email)

    def as_update_tuple(self, student_id: int) -> tuple[str, str, str, int]:
        return (self.first_name, self.last_name, self.email, student_id)


class StudentMapper:
    """
    Data Mapper for the students table.
    Knows how to persist and load Student objects from the DB.
    """

    INSERT_SQL = """
        INSERT INTO students (first_name, last_name, email)
        VALUES (%s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, first_name, last_name, email, registration_date
        FROM students
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, first_name, last_name, email, registration_date
        FROM students
    """

    UPDATE_SQL = """
        UPDATE students
        SET first_name = %s, last_name = %s, email = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM students
        WHERE id = %s
    """

    # ---------- CREATE ----------
    def insert(self, connection: Any, student: Student) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_student") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "students")

            cursor = connection.cursor()
            try:
                cursor.execute(self.INSERT_SQL, student.as_insert_tuple())
                connection.commit()

                student_id = getattr(cursor, "lastrowid", None)
                if student_id is not None:
                    span.set_attribute("student.id", student_id)

                span.set_status(Status(StatusCode.OK))
                return student_id
            except Exception as e:
                # Library-agnostic duplicate detection
                if "Duplicate entry" in str(e):
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, "duplicate_email"))
                    log.warning(
                        "Duplicate email on insert",
                        extra={"student.email": student.email, "error": str(e)},
                    )
                    raise DuplicateEmailError("Email already exists") from e

                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to insert student",
                    extra={"error": str(e), "student.email": student.email},
                )
                raise
            finally:
                cursor.close()

    # ---------- READ ----------
    def get_by_id(self, connection: Any, student_id: int) -> Optional[Student]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_student_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "students")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (student_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                student = self._row_to_student(row)
                span.set_attribute("student.id", student.id)
                span.set_status(Status(StatusCode.OK))
                return student
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch student",
                    extra={"error": str(e), "student.id": student_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[Student]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_students") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "students")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                students = [self._row_to_student(row) for row in rows]
                span.set_attribute("students.count", len(students))
                span.set_status(Status(StatusCode.OK))
                return students
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to list students", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    # ---------- UPDATE ----------
    def update(self, connection: Any, student_id: int, student: Student) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_student") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "students")

            cursor = connection.cursor()
            try:
                cursor.execute(self.UPDATE_SQL, student.as_update_tuple(student_id))
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("student.id", student_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                if "Duplicate entry" in str(e):
                    span.record_exception(e)
                    span.set_status(Status(StatusCode.ERROR, "duplicate_email"))
                    log.warning(
                        "Duplicate email on update",
                        extra={
                            "student.id": student_id,
                            "student.email": student.email,
                            "error": str(e),
                        },
                    )
                    raise DuplicateEmailError("Email already exists") from e

                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update student",
                    extra={"error": str(e), "student.id": student_id},
                )
                raise
            finally:
                cursor.close()

    # ---------- DELETE ----------
    def delete(self, connection: Any, student_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_student") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "students")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (student_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("student.id", student_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete student",
                    extra={"error": str(e), "student.id": student_id},
                )
                raise
            finally:
                cursor.close()

    # ---------- helper ----------
    def _row_to_student(self, row: tuple) -> Student:
        # SELECT id, first_name, last_name, email, registration_date
        student_id, first_name, last_name, email, registration_date = row
        return Student(
            id=student_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            registration_date=registration_date,
        )
