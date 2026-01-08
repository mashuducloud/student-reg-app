import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class WorkplacePlacement:
    id: Optional[int] = None
    student_id: int = 0
    employer_name: str = ""
    employer_contact: Optional[str] = None
    supervisor_name: Optional[str] = None
    supervisor_phone: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None


class WorkplacePlacementMapper:
    INSERT_SQL = """
        INSERT INTO workplace_placements
            (student_id, employer_name, employer_contact,
             supervisor_name, supervisor_phone, start_date, end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, student_id,
               employer_name, employer_contact,
               supervisor_name, supervisor_phone,
               start_date, end_date, created_at
        FROM workplace_placements
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, student_id,
               employer_name, employer_contact,
               supervisor_name, supervisor_phone,
               start_date, end_date, created_at
        FROM workplace_placements
        ORDER BY start_date DESC, id DESC
    """

    UPDATE_SQL = """
        UPDATE workplace_placements
        SET student_id       = %s,
            employer_name    = %s,
            employer_contact = %s,
            supervisor_name  = %s,
            supervisor_phone = %s,
            start_date       = %s,
            end_date         = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM workplace_placements
        WHERE id = %s
    """

    def insert(self, connection: Any, placement: WorkplacePlacement) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_workplace_placement") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "workplace_placements")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        placement.student_id,
                        placement.employer_name,
                        placement.employer_contact,
                        placement.supervisor_name,
                        placement.supervisor_phone,
                        placement.start_date,
                        placement.end_date,
                    ),
                )
                connection.commit()
                pid = getattr(cursor, "lastrowid", None)
                if pid is not None:
                    span.set_attribute("workplace_placement.id", pid)
                span.set_status(Status(StatusCode.OK))
                return pid
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to insert workplace placement",
                    extra={"error": str(e)},
                )
                raise
            finally:
                cursor.close()

    def get_by_id(self, connection: Any, placement_id: int) -> Optional[WorkplacePlacement]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_workplace_placement_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "workplace_placements")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (placement_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                placement = self._row_to_placement(row)
                span.set_attribute("workplace_placement.id", placement.id)
                span.set_status(Status(StatusCode.OK))
                return placement
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch workplace placement",
                    extra={"error": str(e), "workplace_placement.id": placement_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[WorkplacePlacement]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_workplace_placements") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "workplace_placements")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                placements = [self._row_to_placement(r) for r in rows]
                span.set_attribute("workplace_placements.count", len(placements))
                span.set_status(Status(StatusCode.OK))
                return placements
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to list workplace placements",
                    extra={"error": str(e)},
                )
                raise
            finally:
                cursor.close()

    def update(self, connection: Any, placement_id: int, placement: WorkplacePlacement) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_workplace_placement") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "workplace_placements")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        placement.student_id,
                        placement.employer_name,
                        placement.employer_contact,
                        placement.supervisor_name,
                        placement.supervisor_phone,
                        placement.start_date,
                        placement.end_date,
                        placement_id,
                    ),
                )
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("workplace_placement.id", placement_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update workplace placement",
                    extra={"error": str(e), "workplace_placement.id": placement_id},
                )
                raise
            finally:
                cursor.close()

    def delete(self, connection: Any, placement_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_workplace_placement") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "workplace_placements")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (placement_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("workplace_placement.id", placement_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete workplace placement",
                    extra={"error": str(e), "workplace_placement.id": placement_id},
                )
                raise
            finally:
                cursor.close()

    def _row_to_placement(self, row: tuple) -> WorkplacePlacement:
        (
            pid,
            student_id,
            employer_name,
            employer_contact,
            supervisor_name,
            supervisor_phone,
            start_date,
            end_date,
            created_at,
        ) = row

        return WorkplacePlacement(
            id=pid,
            student_id=student_id,
            employer_name=employer_name,
            employer_contact=employer_contact,
            supervisor_name=supervisor_name,
            supervisor_phone=supervisor_phone,
            start_date=start_date,
            end_date=end_date,
            created_at=created_at,
        )
