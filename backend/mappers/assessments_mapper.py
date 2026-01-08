import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, List, Optional

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

log = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


@dataclass
class Assessment:
    id: Optional[int] = None
    student_id: int = 0
    programme_id: int = 0

    assessment_type: str = ""  # formative / summative
    assessment_name: str = ""
    assessment_date: Optional[date] = None

    score: Optional[float] = None
    max_score: Optional[float] = None

    result: Optional[str] = None  # C / NYC or text
    moderation_outcome: Optional[str] = None  # optional text

    created_at: Optional[datetime] = None


class AssessmentMapper:
    INSERT_SQL = """
        INSERT INTO assessments (
            student_id,
            programme_id,
            assessment_type,
            assessment_name,
            assessment_date,
            score,
            max_score,
            result,
            moderation_outcome
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    SELECT_BY_ID_SQL = """
        SELECT
            id,
            student_id,
            programme_id,
            assessment_type,
            assessment_name,
            assessment_date,
            score,
            max_score,
            result,
            moderation_outcome,
            created_at
        FROM assessments
        WHERE id = %s
    """

    SELECT_ALL_SQL = """
        SELECT
            id,
            student_id,
            programme_id,
            assessment_type,
            assessment_name,
            assessment_date,
            score,
            max_score,
            result,
            moderation_outcome,
            created_at
        FROM assessments
        ORDER BY assessment_date DESC, id DESC
    """

    UPDATE_SQL = """
        UPDATE assessments
        SET
            student_id = %s,
            programme_id = %s,
            assessment_type = %s,
            assessment_name = %s,
            assessment_date = %s,
            score = %s,
            max_score = %s,
            result = %s,
            moderation_outcome = %s
        WHERE id = %s
    """

    DELETE_SQL = "DELETE FROM assessments WHERE id = %s"

    # -------------------------------------------------------------
    # INSERT
    # -------------------------------------------------------------
    def insert(self, connection: Any, a: Assessment) -> Optional[int]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_insert_assessment") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "INSERT")
            span.set_attribute("db.sql.table", "assessments")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.INSERT_SQL,
                    (
                        a.student_id,
                        a.programme_id,
                        a.assessment_type,
                        a.assessment_name,
                        a.assessment_date,
                        a.score,
                        a.max_score,
                        a.result,
                        a.moderation_outcome,
                    ),
                )
                connection.commit()

                new_id = getattr(cursor, "lastrowid", None)
                if new_id is not None:
                    span.set_attribute("assessment.id", new_id)

                span.set_status(Status(StatusCode.OK))
                return new_id
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to insert assessment", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    # -------------------------------------------------------------
    # GET BY ID
    # -------------------------------------------------------------
    def get_by_id(self, connection: Any, assessment_id: int) -> Optional[Assessment]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_get_assessment_by_id") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "assessments")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_BY_ID_SQL, (assessment_id,))
                row = cursor.fetchone()

                if not row:
                    span.set_status(Status(StatusCode.OK))
                    return None

                assessment = self._row_to_assessment(row)
                span.set_attribute("assessment.id", assessment.id)
                span.set_status(Status(StatusCode.OK))
                return assessment

            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to fetch assessment",
                    extra={"error": str(e), "assessment.id": assessment_id},
                )
                raise
            finally:
                cursor.close()

    # -------------------------------------------------------------
    # LIST ALL
    # -------------------------------------------------------------
    def list_all(self, connection: Any) -> List[Assessment]:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_list_assessments") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "SELECT")
            span.set_attribute("db.sql.table", "assessments")

            cursor = connection.cursor()
            try:
                cursor.execute(self.SELECT_ALL_SQL)
                rows = cursor.fetchall()
                items = [self._row_to_assessment(r) for r in rows]
                span.set_attribute("assessments.count", len(items))
                span.set_status(Status(StatusCode.OK))
                return items
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error("Failed to list assessments", extra={"error": str(e)})
                raise
            finally:
                cursor.close()

    # -------------------------------------------------------------
    # UPDATE
    # -------------------------------------------------------------
    def update(self, connection: Any, assessment_id: int, a: Assessment) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_update_assessment") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "UPDATE")
            span.set_attribute("db.sql.table", "assessments")

            cursor = connection.cursor()
            try:
                cursor.execute(
                    self.UPDATE_SQL,
                    (
                        a.student_id,
                        a.programme_id,
                        a.assessment_type,
                        a.assessment_name,
                        a.assessment_date,
                        a.score,
                        a.max_score,
                        a.result,
                        a.moderation_outcome,
                        assessment_id,
                    ),
                )

                connection.commit()
                updated = cursor.rowcount > 0

                span.set_attribute("assessment.id", assessment_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))

                return updated

            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to update assessment",
                    extra={"error": str(e), "assessment.id": assessment_id},
                )
                raise
            finally:
                cursor.close()

    # -------------------------------------------------------------
    # DELETE
    # -------------------------------------------------------------
    def delete(self, connection: Any, assessment_id: int) -> bool:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection is not available")

        with tracer.start_as_current_span("db_delete_assessment") as span:
            span.set_attribute("db.system", "mysql")
            span.set_attribute("db.operation", "DELETE")
            span.set_attribute("db.sql.table", "assessments")

            cursor = connection.cursor()
            try:
                cursor.execute(self.DELETE_SQL, (assessment_id,))
                connection.commit()

                deleted = cursor.rowcount > 0

                span.set_attribute("assessment.id", assessment_id)
                span.set_attribute("db.rows_affected", cursor.rowcount)
                span.set_status(Status(StatusCode.OK))

                return deleted
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                log.error(
                    "Failed to delete assessment",
                    extra={"error": str(e), "assessment.id": assessment_id},
                )
                raise
            finally:
                cursor.close()

    # -------------------------------------------------------------
    # INTERNAL: MAP ROW → DATACLASS
    # -------------------------------------------------------------
    def _row_to_assessment(self, row: tuple) -> Assessment:
        (
            a_id,
            student_id,
            programme_id,
            assessment_type,
            assessment_name,
            assessment_date,
            score,
            max_score,
            result,
            moderation_outcome,
            created_at,
        ) = row

        return Assessment(
            id=a_id,
            student_id=student_id,
            programme_id=programme_id,
            assessment_type=assessment_type,
            assessment_name=assessment_name,
            assessment_date=assessment_date,
            score=score,
            max_score=max_score,
            result=result,
            moderation_outcome=moderation_outcome,
            created_at=created_at,
        )
