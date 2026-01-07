# repositories/students_repository.py
import logging
from typing import Dict, List, Optional

from db import get_connection
from mappers.students_mapper import DuplicateEmailError, Student, StudentMapper

log = logging.getLogger(__name__)
_mapper = StudentMapper()


class EmailAlreadyExistsError(Exception):
    """Domain-level exception for duplicate email."""

    pass


def _student_to_dict(student: Student) -> Dict:
    return {
        "id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "email": student.email,
        "registration_date": (student.registration_date.isoformat() if student.registration_date is not None else None),
    }


# ---------- CREATE ----------
def register_student(first_name: str, last_name: str, email: str) -> Optional[int]:
    student = Student(first_name=first_name, last_name=last_name, email=email)

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        try:
            student_id = _mapper.insert(connection, student)
        except DuplicateEmailError as e:
            raise EmailAlreadyExistsError(str(e)) from e

    log.debug(
        "Student persisted in repository",
        extra={"student.email": email, "student.id": student_id},
    )
    return student_id


# ---------- READ ----------
def get_student(student_id: int) -> Optional[Dict]:
    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        student = _mapper.get_by_id(connection, student_id)

    return _student_to_dict(student) if student else None


def list_students() -> List[Dict]:
    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        students = _mapper.list_all(connection)

    return [_student_to_dict(s) for s in students]


# ---------- UPDATE ----------
def update_student(
    student_id: int,
    first_name: str,
    last_name: str,
    email: str,
) -> Optional[Dict]:
    student = Student(first_name=first_name, last_name=last_name, email=email)

    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        try:
            updated = _mapper.update(connection, student_id, student)
        except DuplicateEmailError as e:
            raise EmailAlreadyExistsError(str(e)) from e

        if not updated:
            return None

        fresh = _mapper.get_by_id(connection, student_id)

    return _student_to_dict(fresh) if fresh else None


# ---------- DELETE ----------
def delete_student(student_id: int) -> bool:
    with get_connection() as connection:
        if connection is None or not connection.is_connected():
            raise RuntimeError("DB connection failed")

        deleted = _mapper.delete(connection, student_id)

    return deleted
