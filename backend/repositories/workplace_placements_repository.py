# repositories/workplace_placements_repository.py
import logging
from typing import Any, Dict, List, Optional

from db import get_connection

log = logging.getLogger(__name__)


def _row_to_placement(row: tuple) -> Dict[str, Any]:
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

    return {
        "id": pid,
        "student_id": student_id,
        "employer_name": employer_name,
        "employer_contact": employer_contact,
        "supervisor_name": supervisor_name,
        "supervisor_phone": supervisor_phone,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------- CREATE ----------
def create_placement(
    student_id: int,
    employer_name: str,
    employer_contact: Optional[str] = None,
    supervisor_name: Optional[str] = None,
    supervisor_phone: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> int:
    sql = """
    INSERT INTO workplace_placements (
      student_id,
      employer_name,
      employer_contact,
      supervisor_name,
      supervisor_phone,
      start_date,
      end_date
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s)
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                student_id,
                employer_name,
                employer_contact,
                supervisor_name,
                supervisor_phone,
                start_date,
                end_date,
            ),
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()

    return new_id


# ---------- READ ALL ----------
def list_placements() -> List[Dict[str, Any]]:
    sql = """
    SELECT id, student_id,
           employer_name, employer_contact,
           supervisor_name, supervisor_phone,
           start_date, end_date, created_at
    FROM workplace_placements
    ORDER BY id DESC
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

    return [_row_to_placement(r) for r in rows]


# ---------- READ ONE ----------
def get_placement(placement_id: int) -> Optional[Dict[str, Any]]:
    sql = """
    SELECT id, student_id,
           employer_name, employer_contact,
           supervisor_name, supervisor_phone,
           start_date, end_date, created_at
    FROM workplace_placements
    WHERE id = %s
  """

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (placement_id,))
        row = cursor.fetchone()
        cursor.close()

    return _row_to_placement(row) if row else None


# ---------- UPDATE ----------
def update_placement(
    placement_id: int,
    student_id: int,
    employer_name: str,
    employer_contact: Optional[str],
    supervisor_name: Optional[str],
    supervisor_phone: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
) -> Optional[Dict[str, Any]]:
    sql = """
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

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                student_id,
                employer_name,
                employer_contact,
                supervisor_name,
                supervisor_phone,
                start_date,
                end_date,
                placement_id,
            ),
        )
        connection.commit()
        updated_rows = cursor.rowcount
        cursor.close()

    if updated_rows == 0:
        return None

    return get_placement(placement_id)


# ---------- DELETE ----------
def delete_placement(placement_id: int) -> bool:
    sql = "DELETE FROM workplace_placements WHERE id = %s"

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        cursor = connection.cursor()
        cursor.execute(sql, (placement_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()

    return deleted
