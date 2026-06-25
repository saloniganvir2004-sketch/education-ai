from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from document_registry import (
    get_all_documents,
    get_document_by_id,
    get_document_content,
    delete_document,
    get_document_chunks,
    get_document_pages,
    get_document_overview,
    update_document as update_document_record,
)


router = APIRouter(tags=["Documents"])


class DocumentUpdateRequest(BaseModel):
    subject: str | None = None
    topic: str | None = None
    status: str | None = None


@router.get("/")
def list_documents():
    """
    Unified document management endpoint.
    """

    documents = get_all_documents()

    result = []

    for document in documents:

        if isinstance(document, tuple):
            document_id = document[0]
        else:
            document_id = document.get(
                "document_id"
            )

        result.append(
            {
                "document_id": document_id,
                "document": document,
                "actions": [
                    "view",
                    "edit",
                    "delete"
                ]
            }
        )

    return {
        "count": len(result),
        "documents": result,
    }

@router.get("/{document_id}")
def get_document(document_id: str):
    """
    Returns document details, content, chunks, pages, and available actions.
    """

    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "document": document,
        "overview": get_document_overview(document_id),
        "content": get_document_content(document_id),
        "chunks": get_document_chunks(document_id),
        "pages": get_document_pages(document_id),
        "actions": [
            "edit",
            "delete"
        ]
    }


@router.patch("/{document_id}")
def update_document(
    document_id: str,
    payload: DocumentUpdateRequest
):
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    updated = update_document_record(
        document_id=document_id,
        subject=payload.subject,
        topic=payload.topic,
        status=payload.status
    )
    return {
        "message": "Document update endpoint ready.",
        "document_id": document_id,
        "updated": updated,
        "requested_updates": {
            "subject": payload.subject,
            "topic": payload.topic,
            "status": payload.status,
        },
        "actions": [
            "view",
            "edit",
            "delete"
        ]
    }


@router.delete("/{document_id}")
def remove_document(document_id: str):
    """
    Delete a document.
    """
    document = get_document_by_id(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    deleted = delete_document(document_id)

    if deleted is None:
        deleted = True

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    return {
        "message": "Document deleted successfully."
    }