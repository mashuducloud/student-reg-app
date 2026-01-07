import logging
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# NOTE:
# This is a placeholder implementation so that `main.py` can import
# the document repository functions without crashing.
# Replace the bodies with real DB code once you're ready.


def list_documents() -> List[Dict[str, Any]]:
    """
    Return all documents in the system.

    Placeholder implementation: returns an empty list and logs a warning.
    """
    log.warning("list_documents() called, but documents_repository is not implemented yet.")
    return []


def list_documents_for_student(student_id: int) -> List[Dict[str, Any]]:
    """
    Return all documents for a given student.

    Placeholder implementation: returns an empty list and logs a warning.
    """
    log.warning(
        "list_documents_for_student(%s) called, but documents_repository is not implemented yet.",
        student_id,
    )
    return []


def get_document(document_id: int) -> Optional[Dict[str, Any]]:
    """
    Return a single document by ID, or None if not found.

    Placeholder implementation: always returns None.
    """
    log.warning(
        "get_document(%s) called, but documents_repository is not implemented yet.",
        document_id,
    )
    return None


def create_document(
    student_id: int,
    document_type: str,
    file_name: str,
    file_path: str,
    description: Optional[str] = None,
) -> int:
    """
    Create a new document record and return its ID.

    Placeholder implementation: logs and raises NotImplementedError so you
    don't accidentally rely on it in production.
    """
    log.error("create_document(...) called, but documents_repository is not implemented yet.")
    raise NotImplementedError("create_document is not implemented yet.")


def update_document(
    document_id: int,
    **fields: Any,
) -> Optional[Dict[str, Any]]:
    """
    Update an existing document. Returns the updated document or None.

    Placeholder implementation: logs and raises NotImplementedError.
    """
    log.error(
        "update_document(%s, %s) called, but documents_repository is not implemented yet.",
        document_id,
        fields,
    )
    raise NotImplementedError("update_document is not implemented yet.")


def delete_document(document_id: int) -> bool:
    """
    Delete a document by ID. Returns True if something was deleted.

    Placeholder implementation: logs and raises NotImplementedError.
    """
    log.error(
        "delete_document(%s) called, but documents_repository is not implemented yet.",
        document_id,
    )
    raise NotImplementedError("delete_document is not implemented yet.")
