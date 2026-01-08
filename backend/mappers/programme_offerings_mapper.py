import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class ProgrammeOffering:
    id: Optional[int] = None
    programme_id: int = 0
    name: str = ""
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    max_learners: Optional[int] = None
    funder_type: Optional[str] = None
    seta_project_number: Optional[str] = None
    status: str = "Planned"
    created_at: Optional[datetime] = None


class ProgrammeOfferingMapper:
    INSERT_SQL = """
        INSERT INTO programme_offerings
            (programme_id, name, start_date, end_date, location,
             max_learners, funder_type, seta_project_number, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, programme_id, name, start_date, end_date, location,
               max_learners, funder_type, seta_project_number, status, created_at
        FROM programme_offerings
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, programme_id, name, start_date, end_date, location,
               max_learners, funder_type, seta_project_number, status, created_at
        FROM programme_offerings
        ORDER BY start_date DESC
    """

    UPDATE_SQL = """
        UPDATE programme_offerings
        SET programme_id = %s,
            name = %s,
            start_date = %s,
            end_date = %s,
            location = %s,
            max_learners = %s,
            funder_type = %s,
            seta_project_number = %s,
            status = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM programme_offerings
        WHERE id = %s
    """

    def insert(self, connection: Any, offering: ProgrammeOffering) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_programme_offering") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "programme_offerings")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        offering.programme_id,
                        offering.name,
                        offering.start_date,
                        offering.end_date,
                        offering.location,
                        offering.max_learners,
                        offering.funder_type,
                        offering.seta_project_number,
                        offering.status,
                    ),
                )
                connection.commit()
                oid = getattr(cursor, "lastrowid", None)
                if oid is not None:
                    span.set_attribute("programme_offering.id", oid)
                span.set_status(Status(StatusCode.OK))
                return oid
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to insert programme offering", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def get_by_id(self, connection: Any, offering_id: int) -> Optional[ProgrammeOffering]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_programme_offering_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "programme_offerings")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (offering_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                offering = self._row_to_offering(row)
                span.set_attribute("programme_offering.id", offering.id)
                span.set_status(Status(StatusCode.OK))
                return offering
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch programme offering",
                    extra={"error": str(e), "programme_offering.id": offering_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[ProgrammeOffering]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_programme_offerings") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "programme_offerings")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                offerings = [self._row_to_offering(r) for r in rows]
                span.set_attribute("programme_offerings.count", len(offerings))
                span.set_status(Status(StatusCode.OK))
                return offerings
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to list programme offerings",
                    extra={"error": str(e)},
                )
                raise
            finally:
                cursor.close()

    def update(self, connection: Any, offering_id: int, offering: ProgrammeOffering) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_programme_offering") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "programme_offerings")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        offering.programme_id,
                        offering.name,
                        offering.start_date,
                        offering.end_date,
                        offering.location,
                        offering.max_learners,
                        offering.funder_type,
                        offering.seta_project_number,
                        offering.status,
                        offering_id,
                    ),
                )
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("programme_offering.id", offering_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update programme offering",
                    extra={"error": str(e), "programme_offering.id": offering_id},
                )
                raise
            finally:
                cursor.close()

    def delete(self, connection: Any, offering_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_programme_offering") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "programme_offerings")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (offering_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("programme_offering.id", offering_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete programme offering",
                    extra={"error": str(e), "programme_offering.id": offering_id},
                )
                raise
            finally:
                cursor.close()

    def _row_to_offering(self, row: tuple) -> ProgrammeOffering:
        (
            oid,
            programme_id,
            name,
            start_date,
            end_date,
            location,
            max_learners,
            funder_type,
            seta_project_number,
            status,
            created_at,
        ) = row

        return ProgrammeOffering(
            id=oid,
            programme_id=programme_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            location=location,
            max_learners=max_learners,
            funder_type=funder_type,
            seta_project_number=seta_project_number,
            status=status,
            created_at=created_at,
        )
