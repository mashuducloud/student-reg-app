import logging
from typing import Any, Dict, List, Optional

from db import create_db_connection
from mysql.connector import Error as MySQLError

log = logging.getLogger(__name__)


class ProgrammeCodeAlreadyExistsError(Exception):
    """Raised when trying to create/update a programme with a duplicate code."""

    pass


def _row_to_dict(row) -> Dict[str, Any]:
    """
    Convert a DB row (tuple) to a programme dict.
    Order must match SELECT clause.
    """
    (
        pid,
        programme_code,
        programme_name,
        nqf_level,
        credits,
        description,
        is_active,
        created_at,
    ) = row

    return {
        "id": pid,
        "programme_code": programme_code,
        "programme_name": programme_name,
        "nqf_level": nqf_level,
        "credits": credits,
        "description": description,
        "is_active": bool(is_active),
        "created_at": created_at.isoformat() if created_at else None,
    }


# ---------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------


def list_programmes() -> List[Dict[str, Any]]:
    """
    Return all programmes as a list of dicts.
    """
    conn = None
    cursor = None
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                programme_code,
                programme_name,
                nqf_level,
                credits,
                description,
                is_active,
                created_at
            FROM programmes
            ORDER BY programme_name ASC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return [_row_to_dict(row) for row in rows]

    except MySQLError:
        log.exception("Error listing programmes from DB")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_programme(programme_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single programme by ID.
    Returns dict or None.
    """
    conn = None
    cursor = None
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT
                id,
                programme_code,
                programme_name,
                nqf_level,
                credits,
                description,
                is_active,
                created_at
            FROM programmes
            WHERE id = %s
        """
        cursor.execute(query, (programme_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return _row_to_dict(row)

    except MySQLError:
        log.exception("Error fetching programme id=%s", programme_id)
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _ensure_unique_code(conn, programme_code: str, exclude_id: Optional[int] = None):
    """
    Ensure programme_code is unique. If exclude_id is provided, ignore that record.
    Raises ProgrammeCodeAlreadyExistsError if a conflict exists.
    """
    cursor = conn.cursor()
    try:
        if exclude_id is not None:
            query = """
                SELECT id
                FROM programmes
                WHERE programme_code = %s
                  AND id <> %s
                LIMIT 1
            """
            cursor.execute(query, (programme_code, exclude_id))
        else:
            query = """
                SELECT id
                FROM programmes
                WHERE programme_code = %s
                LIMIT 1
            """
            cursor.execute(query, (programme_code,))

        row = cursor.fetchone()
        if row:
            raise ProgrammeCodeAlreadyExistsError(f"Programme code '{programme_code}' already exists")
    finally:
        cursor.close()


def create_programme(
    programme_name: str,
    programme_code: str,
    nqf_level: Optional[int] = None,
    credits: Optional[int] = None,
    description: Optional[str] = None,
) -> int:
    """
    Insert a new programme and return its new ID.
    """
    conn = None
    cursor = None
    try:
        conn = create_db_connection()

        # Check uniqueness of programme_code
        _ensure_unique_code(conn, programme_code)

        cursor = conn.cursor()
        query = """
            INSERT INTO programmes (
                programme_code,
                programme_name,
                nqf_level,
                credits,
                description,
                is_active
            )
            VALUES (%s, %s, %s, %s, %s, 1)
        """
        cursor.execute(
            query,
            (
                programme_code,
                programme_name,
                nqf_level,
                credits,
                description,
            ),
        )
        conn.commit()
        return cursor.lastrowid

    except ProgrammeCodeAlreadyExistsError:
        # Let the caller handle this explicitly
        raise
    except MySQLError:
        log.exception("Error creating programme in DB")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def update_programme(
    programme_id: int,
    programme_name: str,
    programme_code: str,
    nqf_level: Optional[int] = None,
    credits: Optional[int] = None,
    description: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing programme. Returns updated dict, or None if not found.
    """
    conn = None
    cursor = None
    try:
        conn = create_db_connection()

        # Ensure code uniqueness (excluding this programme)
        _ensure_unique_code(conn, programme_code, exclude_id=programme_id)

        cursor = conn.cursor()
        query = """
            UPDATE programmes
            SET
                programme_code = %s,
                programme_name = %s,
                nqf_level = %s,
                credits = %s,
                description = %s
            WHERE id = %s
        """
        cursor.execute(
            query,
            (
                programme_code,
                programme_name,
                nqf_level,
                credits,
                description,
                programme_id,
            ),
        )
        conn.commit()

        if cursor.rowcount == 0:
            # No rows updated => not found
            return None

        return get_programme(programme_id)

    except ProgrammeCodeAlreadyExistsError:
        raise
    except MySQLError:
        log.exception("Error updating programme id=%s", programme_id)
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def delete_programme(programme_id: int) -> bool:
    """
    Delete a programme by ID.
    Returns True if deleted, False if not found.
    """
    conn = None
    cursor = None
    try:
        conn = create_db_connection()
        cursor = conn.cursor()

        query = "DELETE FROM programmes WHERE id = %s"
        cursor.execute(query, (programme_id,))
        conn.commit()

        return cursor.rowcount > 0

    except MySQLError:
        log.exception("Error deleting programme id=%s", programme_id)
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
