# repositories/assessments_repository.py
import logging
from typing import Any, Dict, List, Optional

from db import get_connection

log = logging.getLogger(__name__)


def _row_to_assessment(row: tuple) -> Dict[str, Any]:
    (
        aid,
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

    return {
        "id": aid,
        "student_id": student_id,
        "programme_id": programme_id,
        "assessment_type": assessment_type,
        "assessment_name": assessment_name,
        "assessment_date": assessment_date.isoformat() if assessment_date else None,
        "score": float(score) if score is not None else None,
        "max_score": float(max_score) if max_score is not None else None,
        "result": result,
        "moderation_outcome": moderation_outcome,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------- CREATE ----------
def create_assessment(
    student_id: int,
    programme_id: int,
    assessment_type: str,
    assessment_name: str,
    assessment_date: Optional[str] = None,  # "YYYY-MM-DD"
    score: Optional[float] = None,
    max_score: Optional[float] = None,
    result: Optional[str] = None,
    moderation_outcome: Optional[str] = None,
) -> int:
    sql = """
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

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                student_id,
                programme_id,
                assessment_type,
                assessment_name,
                assessment_date,
                score,
                max_score,
                result,
                moderation_outcome,
            ),
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()

    return new_id


# ---------- READ ALL ----------
def list_assessments() -> List[Dict[str, Any]]:
    sql = """
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

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_assessment(r) for r in rows]


# ---------- READ ONE ----------
def get_assessment(assessment_id: int) -> Optional[Dict[str, Any]]:
    sql = """
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

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (assessment_id,))
        row = cursor.fetchone()
        cursor.close()

    return _row_to_assessment(row) if row else None


# ---------- UPDATE ----------
def update_assessment(
    assessment_id: int,
    student_id: int,
    programme_id: int,
    assessment_type: str,
    assessment_name: str,
    assessment_date: Optional[str],
    score: Optional[float],
    max_score: Optional[float],
    result: Optional[str],
    moderation_outcome: Optional[str],
) -> Optional[Dict[str, Any]]:
    sql = """
        UPDATE assessments
        SET
            student_id        = %s,
            programme_id      = %s,
            assessment_type   = %s,
            assessment_name   = %s,
            assessment_date   = %s,
            score             = %s,
            max_score         = %s,
            result            = %s,
            moderation_outcome = %s
        WHERE id = %s
    """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                student_id,
                programme_id,
                assessment_type,
                assessment_name,
                assessment_date,
                score,
                max_score,
                result,
                moderation_outcome,
                assessment_id,
            ),
        )
        connection.commit()
        updated_rows = cursor.rowcount
        cursor.close()

    if updated_rows == 0:
        return None

    return get_assessment(assessment_id)


# ---------- DELETE ----------
def delete_assessment(assessment_id: int) -> bool:
    sql = "DELETE FROM assessments WHERE id = %s"

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (assessment_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted
