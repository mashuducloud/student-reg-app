import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class Workplace:
    id: Optional[int] = None
    employer_id: int = 0
    site_name: str = ""
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal_code: Optional[str] = None
    approved_by_mict: bool = False
    created_at: Optional[datetime] = None


class WorkplaceMapper:
    INSERT_SQL = """
        INSERT INTO workplaces
            (employer_id, site_name, address_line1, address_line2,
             city, province, postal_code, approved_by_mict)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, employer_id, site_name, address_line1, address_line2,
               city, province, postal_code, approved_by_mict, created_at
        FROM workplaces
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, employer_id, site_name, address_line1, address_line2,
               city, province, postal_code, approved_by_mict, created_at
        FROM workplaces
        ORDER BY site_name
    """

    UPDATE_SQL = """
        UPDATE workplaces
        SET employer_id = %s,
            site_name = %s,
            address_line1 = %s,
            address_line2 = %s,
            city = %s,
            province = %s,
            postal_code = %s,
            approved_by_mict = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM workplaces
        WHERE id = %s
    """

    def insert(self, connection: Any, workplace: Workplace) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_workplace") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "workplaces")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        workplace.employer_id,
                        workplace.site_name,
                        workplace.address_line1,
                        workplace.address_line2,
                        workplace.city,
                        workplace.province,
                        workplace.postal_code,
                        1 if workplace.approved_by_mict else 0,
                    ),
                )
                connection.commit()
                wid = getattr(cursor, "lastrowid", None)
                if wid is not None:
                    span.set_attribute("workplace.id", wid)
                span.set_status(Status(StatusCode.OK))
                return wid
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to insert workplace", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def get_by_id(self, connection: Any, workplace_id: int) -> Optional[Workplace]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_workplace_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "workplaces")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (workplace_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                workplace = self._row_to_workplace(row)
                span.set_attribute("workplace.id", workplace.id)
                span.set_status(Status(StatusCode.OK))
                return workplace
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch workplace",
                    extra={"error": str(e), "workplace.id": workplace_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[Workplace]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_workplaces") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "workplaces")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                workplaces = [self._row_to_workplace(r) for r in rows]
                span.set_attribute("workplaces.count", len(workplaces))
                span.set_status(Status(StatusCode.OK))
                return workplaces
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to list workplaces", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def update(self, connection: Any, workplace_id: int, workplace: Workplace) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_workplace") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "workplaces")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        workplace.employer_id,
                        workplace.site_name,
                        workplace.address_line1,
                        workplace.address_line2,
                        workplace.city,
                        workplace.province,
                        workplace.postal_code,
                        1 if workplace.approved_by_mict else 0,
                        workplace_id,
                    ),
                )
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("workplace.id", workplace_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update workplace",
                    extra={"error": str(e), "workplace.id": workplace_id},
                )
                raise
            finally:
                cursor.close()

    def delete(self, connection: Any, workplace_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_workplace") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "workplaces")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (workplace_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("workplace.id", workplace_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete workplace",
                    extra={"error": str(e), "workplace.id": workplace_id},
                )
                raise
            finally:
                cursor.close()

    def _row_to_workplace(self, row: tuple) -> Workplace:
        (
            wid,
            employer_id,
            site_name,
            address_line1,
            address_line2,
            city,
            province,
            postal_code,
            approved_by_mict,
            created_at,
        ) = row

        return Workplace(
            id=wid,
            employer_id=employer_id,
            site_name=site_name,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            province=province,
            postal_code=postal_code,
            approved_by_mict=bool(approved_by_mict),
            created_at=created_at,
        )
