import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class StipendRecord:
    id: Optional[int] = None
    student_id: int = 0
    period_start: date | None = None
    period_end: date | None = None
    attendance_percentage: Optional[float] = None
    amount: float = 0.0
    status: str = "Draft"  # Draft → Submitted → Approved / Rejected
    created_at: Optional[datetime] = None


class StipendRecordMapper:
    INSERT_SQL = """
        INSERT INTO stipend_records
            (student_id, period_start, period_end,
             attendance_percentage, amount, status)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    SELECT_BY_ID_SQL = """
        SELECT id, student_id, period_start, period_end,
               attendance_percentage, amount, status, created_at
        FROM stipend_records
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT id, student_id, period_start, period_end,
               attendance_percentage, amount, status, created_at
        FROM stipend_records
        ORDER BY period_start DESC
    """

    UPDATE_SQL = """
        UPDATE stipend_records
        SET student_id = %s,
            period_start = %s,
            period_end = %s,
            attendance_percentage = %s,
            amount = %s,
            status = %s
        WHERE id = %s
    """

    DELETE_SQL = """
        DELETE FROM stipend_records
        WHERE id = %s
    """

    def insert(self, connection: Any, record: StipendRecord) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_stipend_record") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "stipend_records")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        record.student_id,
                        record.period_start,
                        record.period_end,
                        record.attendance_percentage,
                        record.amount,
                        record.status,
                    ),
                )
                connection.commit()
                rid = getattr(cursor, "lastrowid", None)
                if rid is not None:
                    span.set_attribute("stipend_record.id", rid)
                span.set_status(Status(StatusCode.OK))
                return rid
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to insert stipend record", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def get_by_id(self, connection: Any, record_id: int) -> Optional[StipendRecord]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_stipend_record_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "stipend_records")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (record_id,))
                row = cursor.fetchone()
                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                record = self._row_to_record(row)
                span.set_attribute("stipend_record.id", record.id)
                span.set_status(Status(StatusCode.OK))
                return record
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch stipend record",
                    extra={"error": str(e), "stipend_record.id": record_id},
                )
                raise
            finally:
                cursor.close()

    def list_all(self, connection: Any) -> List[StipendRecord]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_stipend_records") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "stipend_records")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                records = [self._row_to_record(r) for r in rows]
                span.set_attribute("stipend_records.count", len(records))
                span.set_status(Status(StatusCode.OK))
                return records
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to list stipend records", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    def update(self, connection: Any, record_id: int, record: StipendRecord) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_stipend_record") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "stipend_records")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        record.student_id,
                        record.period_start,
                        record.period_end,
                        record.attendance_percentage,
                        record.amount,
                        record.status,
                        record_id,
                    ),
                )
                connection.commit()
                updated = cursor.rowcount > 0
                span.set_attribute("stipend_record.id", record_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return updated
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update stipend record",
                    extra={"error": str(e), "stipend_record.id": record_id},
                )
                raise
            finally:
                cursor.close()

    def delete(self, connection: Any, record_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_stipend_record") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "stipend_records")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (record_id,))
                connection.commit()
                deleted = cursor.rowcount > 0
                span.set_attribute("stipend_record.id", record_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))
                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete stipend record",
                    extra={"error": str(e), "stipend_record.id": record_id},
                )
                raise
            finally:
                cursor.close()

    def _row_to_record(self, row: tuple) -> StipendRecord:
        (
            rid,
            student_id,
            period_start,
            period_end,
            attendance_percentage,
            amount,
            status,
            created_at,
        ) = row

        return StipendRecord(
            id=rid,
            student_id=student_id,
            period_start=period_start,
            period_end=period_end,
            attendance_percentage=attendance_percentage,
            amount=float(amount),
            status=status,
            created_at=created_at,
        )
