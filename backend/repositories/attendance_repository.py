# repositories/attendance_repository.py
import logging
from typing import Any, Dict, List, Optional

from db import get_connection

log = logging.getLogger(__name__)


def _row_to_attendance(row: tuple) -> Dict[str, Any]:
    (aid, student_id, attendance_date, status, created_at) = row

    return {
        "id": aid,
        "student_id": student_id,
        "attendance_date": attendance_date.isoformat() if attendance_date else None,
        "status": status,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------- CREATE ----------
def create_attendance(
    student_id: int,
    attendance_date: str,  # 'YYYY-MM-DD'
    status: str = "present",
) -> int:
    """
    Insert an attendance row and return its ID.
    """
    sql = """
    INSERT INTO attendance (student_id, attendance_date, status)
    VALUES (%s, %s, %s)
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id, attendance_date, status))
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()

    return new_id


# ---------- READ ALL ----------
def list_attendance() -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, attendance_date, status, created_at
    FROM attendance
    ORDER BY attendance_date DESC, student_id ASC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_attendance(r) for r in rows]


# ---------- READ BY STUDENT ----------
def list_attendance_for_student(student_id: int) -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, attendance_date, status, created_at
    FROM attendance
    WHERE student_id = %s
    ORDER BY attendance_date DESC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id,))
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_attendance(r) for r in rows]


# ---------- UPDATE ----------
def update_attendance(
    attendance_id: int,
    student_id: int,
    attendance_date: str,
    status: str,
) -> Optional[Dict[str, Any]]:
    sql = """
    UPDATE attendance
    SET student_id      = %s,
        attendance_date = %s,
        status          = %s
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id, attendance_date, status, attendance_id))
        connection.commit()
        updated_rows = cursor.rowcount
        cursor.close()

    if updated_rows == 0:
        return None

    return get_attendance(attendance_id)


# ---------- READ ONE ----------
def get_attendance(attendance_id: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, attendance_date, status, created_at
    FROM attendance
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (attendance_id,))
        row = cursor.fetchone()
        cursor.close()

    return _row_to_attendance(row) if row else None


# ---------- DELETE ----------
def delete_attendance(attendance_id: int) -> bool:
    sql = "DELETE FROM attendance WHERE id = %s"

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (attendance_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted
