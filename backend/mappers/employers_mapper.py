import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class Employer:
    id: Optional[int] = None
    name: str = ""
    reg_number: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    created_at: Optional[datetime] = None


class EmployerMapper:
    INSERT_SQL = """
        INSERT INTO employers (name, reg_number, contact_person, contact_email, contact_phone)
        VALUES (%s, %s, %s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, name, reg_number, contact_person, contact_email, contact_phone, created_at
        FROM employers
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, name, reg_number, contact_person, contact_email, contact_phone, created_at
        FROM employers
        ORDER BY name
    """

    UPDATE_SQL = """
        UPDATE employers
        SET name = %s,
            reg_number = %s,
            contact_person = %s,
            contact_email = %s,
            contact_phone = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM employers
        WHERE id = %s
    """

    def insert(self, connection: Any, employer: Employer) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_employer") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "employers")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        employer.name,
                        employer.reg_number,
                        employer.contact_person,
                        employer.contact_email,
                        employer.contact_phone,
                    ),
                )
                connection.commit()
                eid = getattr(cursor, "lastrowid", None)
                if eid is not None:
                    span.set_attribute("employer.id", eid)
                span.set_status(Status(StatusCode.OK))
                return eid
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to insert employer", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def get_by_id(self, connection: Any, employer_id: int) -> Optional[Employer]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_employer_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "employers")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (employer_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                employer = self._row_to_employer(row)
                span.set_attribute("employer.id", employer.id)
                span.set_status(Status(StatusCode.OK))
                return employer
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch employer",
                    extra={"error": str(e), "employer.id": employer_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[Employer]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_employers") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "employers")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                employers = [self._row_to_employer(r) for r in rows]
                span.set_attribute("employers.count", len(employers))
                span.set_status(Status(StatusCode.OK))
                return employers
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to list employers", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def update(self, connection: Any, employer_id: int, employer: Employer) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_employer") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "employers")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        employer.name,
                        employer.reg_number,
                        employer.contact_person,
                        employer.contact_email,
                        employer.contact_phone,
                        employer_id,
                    ),
                )
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("employer.id", employer_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update employer",
                    extra={"error": str(e), "employer.id": employer_id},
                )
                raise
            finally:
                cursor.close()

    def delete(self, connection: Any, employer_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_employer") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "employers")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (employer_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("employer.id", employer_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete employer",
                    extra={"error": str(e), "employer.id": employer_id},
                )
                raise
            finally:
                cursor.close()

    def _row_to_employer(self, row: tuple) -> Employer:
        (
            eid,
            name,
            reg_number,
            contact_person,
            contact_email,
            contact_phone,
            created_at,
        ) = row
        return Employer(
            id=eid,
            name=name,
            reg_number=reg_number,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone,
            created_at=created_at,
        )
