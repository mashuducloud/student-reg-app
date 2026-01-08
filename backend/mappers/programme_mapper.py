from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from mysql.connector import MySQLConnection


@dataclass
class Programme:
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    nqf_level: Optional[int] = None
    credits: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None

    # These are *not* in the DB yet – kept here for future compatibility
    qualification_id: Optional[int] = None
    programme_type: Optional[str] = None


class ProgrammeMapper:
    """
    Handles DB <-> Programme mapping for the `programmes` table.

    Current table:

        CREATE TABLE programmes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(50) NOT NULL,
            name VARCHAR(255) NOT NULL,
            nqf_level TINYINT NULL,
            credits INT NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """

    # ---------- internal helper ----------

    def _row_to_programme(self, row: dict) -> Programme:
        return Programme(
            id=row["id"],
            code=row["code"],
            name=row["name"],
            nqf_level=row.get("nqf_level"),
            credits=row.get("credits"),
            is_active=bool(row["is_active"]),
            created_at=row.get("created_at"),
        )

    # ---------- READ ALL ----------

    def list_all(self, connection: MySQLConnection) -> List[Programme]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                id,
                code,
                name,
                nqf_level,
                credits,
                is_active,
                created_at
            FROM programmes
            ORDER BY name
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        return [self._row_to_programme(r) for r in rows]

    # ---------- READ ONE ----------

    def get_by_id(
        self,
        connection: MySQLConnection,
        programme_id: int,
    ) -> Optional[Programme]:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                id,
                code,
                name,
                nqf_level,
                credits,
                is_active,
                created_at
            FROM programmes
            WHERE id = %s
            """,
            (programme_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return self._row_to_programme(row) if row else None

    # ---------- CREATE ----------

    def insert(
        self,
        connection: MySQLConnection,
        programme: Programme,
    ) -> int:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO programmes (code, name, nqf_level, credits, is_active)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                programme.code,
                programme.name,
                programme.nqf_level,
                programme.credits,
                int(programme.is_active),
            ),
        )
        connection.commit()
        new_id = cursor.lastrowid
        cursor.close()
        return new_id

    # ---------- UPDATE ----------

    def update(
        self,
        connection: MySQLConnection,
        programme_id: int,
        programme: Programme,
    ) -> bool:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE programmes
            SET
                code = %s,
                name = %s,
                nqf_level = %s,
                credits = %s,
                is_active = %s
            WHERE id = %s
            """,
            (
                programme.code,
                programme.name,
                programme.nqf_level,
                programme.credits,
                int(programme.is_active),
                programme_id,
            ),
        )
        connection.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        return updated

    # ---------- DELETE ----------

    def delete(self, connection: MySQLConnection, programme_id: int) -> bool:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM programmes WHERE id = %s", (programme_id,))
        connection.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        return deleted
