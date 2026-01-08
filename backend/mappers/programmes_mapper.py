# backend/mappers/programme_mapper.py
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from mysql.connector import Error

log = logging.getLogger(__name__)


@dataclass
class Programme:
    id: Optional[int] = None
    code: Optional[str] = None
    name: Optional[str] = None
    nqf_level: Optional[int] = None
    credits: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    # These remain for future use, but are NOT mapped to DB columns yet.
    qualification_id: Optional[int] = None
    programme_type: Optional[str] = None
    created_at: Optional[datetime] = None


class ProgrammeMapper:
    """
    Low-level mapper for the `programmes` table.
    This class knows how to translate DB rows <-> Programme objects.
    """

    def _row_to_programme(self, row: Dict[str, Any]) -> Programme:
        return Programme(
            id=row.get("id"),
            code=row.get("code"),
            name=row.get("name"),
            nqf_level=row.get("nqf_level"),
            credits=row.get("credits"),
            description=row.get("description"),
            is_active=bool(row.get("is_active", 1)),
            created_at=row.get("created_at"),
        )

    # ---------- CREATE ----------
    def insert(self, connection, programme: Programme) -> int:
        """
        Insert a Programme into the DB.
        Returns the newly generated ID.
        """
        sql = """
            INSERT INTO programmes
                (code, name, nqf_level, credits, description, is_active)
            VALUES
                (%s, %s, %s, %s, %s, %s)
        """

        params = (
            programme.code,
            programme.name,
            programme.nqf_level,
            programme.credits,
            programme.description,
            1 if programme.is_active else 0,
        )

        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            connection.commit()
            new_id = cursor.lastrowid
            log.debug("Inserted programme id=%s", new_id)
            return new_id
        except Error:
            log.exception("Failed to insert programme")
            connection.rollback()
            raise
        finally:
            cursor.close()

    # ---------- READ ALL ----------
    def list_all(self, connection) -> List[Programme]:
        sql = """
            SELECT
                id,
                code,
                name,
                nqf_level,
                credits,
                description,
                is_active,
                created_at
            FROM programmes
            ORDER BY name ASC, id ASC
        """

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [self._row_to_programme(row) for row in rows]
        except Error:
            log.exception("Failed to list programmes")
            raise
        finally:
            cursor.close()

    # ---------- READ ONE ----------
    def get_by_id(self, connection, programme_id: int) -> Optional[Programme]:
        sql = """
            SELECT
                id,
                code,
                name,
                nqf_level,
                credits,
                description,
                is_active,
                created_at
            FROM programmes
            WHERE id = %s
        """

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(sql, (programme_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_programme(row)
        except Error:
            log.exception("Failed to fetch programme id=%s", programme_id)
            raise
        finally:
            cursor.close()

    # ---------- UPDATE ----------
    def update(self, connection, programme_id: int, programme: Programme) -> bool:
        """
        Update an existing programme.
        Returns True if a row was updated, False if not found.
        """
        sql = """
            UPDATE programmes
            SET
                code = %s,
                name = %s,
                nqf_level = %s,
                credits = %s,
                description = %s,
                is_active = %s
            WHERE id = %s
        """

        params = (
            programme.code,
            programme.name,
            programme.nqf_level,
            programme.credits,
            programme.description,
            1 if programme.is_active else 0,
            programme_id,
        )

        cursor = connection.cursor()
        try:
            cursor.execute(sql, params)
            connection.commit()
            updated = cursor.rowcount > 0
            log.debug("Updated programme id=%s, updated=%s", programme_id, updated)
            return updated
        except Error:
            log.exception("Failed to update programme id=%s", programme_id)
            connection.rollback()
            raise
        finally:
            cursor.close()

    # ---------- DELETE ----------
    def delete(self, connection, programme_id: int) -> bool:
        """
        Delete a programme by ID.
        Returns True if a row was deleted, False otherwise.
        """
        sql = "DELETE FROM programmes WHERE id = %s"

        cursor = connection.cursor()
        try:
            cursor.execute(sql, (programme_id,))
            connection.commit()
            deleted = cursor.rowcount > 0
            log.debug("Deleted programme id=%s, deleted=%s", programme_id, deleted)
            return deleted
        except Error:
            log.exception("Failed to delete programme id=%s", programme_id)
            connection.rollback()
            raise
        finally:
            cursor.close()
