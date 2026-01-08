# repositories/stipends_repository.py
import logging
from typing import Any, Dict, List, Optional

from db import get_connection

log = logging.getLogger(__name__)


def _row_to_stipend(row: tuple) -> Dict[str, Any]:
    (sid, student_id, month, amount, status, created_at) = row

    return {
        "id": sid,
        "student_id": student_id,
        "month": month,
        "amount": float(amount) if amount is not None else 0.0,
        "status": status,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------- CREATE ----------
def create_stipend(
    student_id: int,
    month: str,  # 'YYYY-MM'
    amount: float,
    status: str = "submitted",
) -> int:
    sql = """
    INSERT INTO stipends (student_id, month, amount, status)
    VALUES (%s, %s, %s, %s)
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id, month, amount, status))
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()

    return new_id


# ---------- READ ALL ----------
def list_stipends() -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, month, amount, status, created_at
    FROM stipends
    ORDER BY month DESC, student_id ASC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_stipend(r) for r in rows]


# ---------- READ BY STUDENT ----------
def list_stipends_for_student(student_id: int) -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, month, amount, status, created_at
    FROM stipends
    WHERE student_id = %s
    ORDER BY month DESC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id,))
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_stipend(r) for r in rows]


# ---------- UPDATE ----------
def update_stipend(
    stipend_id: int,
    student_id: int,
    month: str,
    amount: float,
    status: str,
) -> Optional[Dict[str, Any]]:
    sql = """
    UPDATE stipends
    SET student_id = %s,
        month      = %s,
        amount     = %s,
        status     = %s
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (student_id, month, amount, status, stipend_id))
        connection.commit()
        updated_rows = cursor.rowcount
        cursor.close()

    if updated_rows == 0:
        return None

    return get_stipend(stipend_id)


# ---------- READ ONE ----------
def get_stipend(stipend_id: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, student_id, month, amount, status, created_at
    FROM stipends
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (stipend_id,))
        row = cursor.fetchone()
        cursor.close()

    return _row_to_stipend(row) if row else None


# ---------- DELETE ----------
def delete_stipend(stipend_id: int) -> bool:
    sql = "DELETE FROM stipends WHERE id = %s"

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (stipend_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted
