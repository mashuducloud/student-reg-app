# repositories/enrolments_repository.py
import logging
from typing import Any, Dict, List, Optional

from db import get_connection

log = logging.getLogger(__name__)


def _row_to_enrolment(row: tuple) -> Dict[str, Any]:
    (
        eid,
        student_id,
        programme_id,
        enrolment_status,
        enrolment_date,
        completion_date,
        created_at,
    ) = row

    return {
        "id": eid,
        "student_id": student_id,
        "programme_id": programme_id,
        "enrolment_status": enrolment_status,
        "enrolment_date": enrolment_date.isoformat() if enrolment_date else None,
        "completion_date": completion_date.isoformat() if completion_date else None,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------- CREATE ----------
def create_enrolment(
    student_id: int,
    programme_id: int,
    enrolment_status: str = "applied",
    enrolment_date: Optional[str] = None,  # 'YYYY-MM-DD'
    completion_date: Optional[str] = None,
) -> int:
    """
    Insert an enrolment row and return its ID.
    """
    sql = """
    INSERT INTO enrolments (
      student_id,
      programme_id,
      enrolment_status,
      enrolment_date,
      completion_date
    )
    VALUES (%s, %s, %s, %s, %s)
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(
            sql,
            (student_id, programme_id, enrolment_status, enrolment_date, completion_date),
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()

    return new_id


# ---------- READ ALL ----------
def list_enrolments() -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, programme_id,
           enrolment_status, enrolment_date, completion_date, created_at
    FROM enrolments
    ORDER BY id DESC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_enrolment(r) for r in rows]


# ---------- READ ONE ----------
def get_enrolment(enrolment_id: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, programme_id,
           enrolment_status, enrolment_date, completion_date, created_at
    FROM enrolments
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (enrolment_id,))
        row = cursor.fetchone()
        cursor.close()

    return _row_to_enrolment(row) if row else None


# ---------- UPDATE ----------
def update_enrolment(
    enrolment_id: int,
    student_id: int,
    programme_id: int,
    enrolment_status: str,
    enrolment_date: Optional[str],
    completion_date: Optional[str],
) -> Optional[Dict[str, Any]]:
    sql = """
    UPDATE enrolments
    SET student_id       = %s,
        programme_id     = %s,
        enrolment_status = %s,
        enrolment_date   = %s,
        completion_date  = %s
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
                enrolment_status,
                enrolment_date,
                completion_date,
                enrolment_id,
            ),
        )
        connection.commit()
        updated_rows = cursor.rowcount
        cursor.close()

    if updated_rows == 0:
        return None

    return get_enrolment(enrolment_id)


# ---------- DELETE ----------
def delete_enrolment(enrolment_id: int) -> bool:
    sql = "DELETE FROM enrolments WHERE id = %s"

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (enrolment_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted
