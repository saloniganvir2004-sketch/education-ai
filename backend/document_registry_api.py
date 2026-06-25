from fastapi import APIRouter, HTTPException

from document_registry import (
    get_document,
    get_documents,
    get_documents_by_topic,
    update_document_status,
    delete_document_registry_entry
)

from vector_store import delete_document_chunks
from qa_db import delete_document_qa_pairs
from upload_history_db import delete_uploaded_file

router = APIRouter(
    prefix="/documents",
    tags=["Document Registry"]
)


@router.get("/")
def list_documents():

    rows = get_documents()

    documents = []

    for row in rows:
        documents.append(
            {
                "document_id": row[0],
                "parent_id": row[1],
                "filename": row[2],
                "subject": row[3],
                "topic": row[4],
                "chunk_count": row[5],
                "status": row[6],
                "created_at": row[7]
            }
        )

    return {
        "count": len(documents),
        "documents": documents
    }


@router.get("/{document_id}")
def read_document(document_id: str):

    row = get_document(document_id)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    return {
        "document_id": row[0],
        "parent_id": row[1],
        "filename": row[2],
        "subject": row[3],
        "topic": row[4],
        "chunk_count": row[5],
        "status": row[6],
        "created_at": row[7]
    }


@router.get("/topic/{subject}/{topic}")
def read_documents_by_topic(
    subject: str,
    topic: str
):

    rows = get_documents_by_topic(
        subject,
        topic
    )

    documents = []

    for row in rows:
        documents.append(
            {
                "document_id": row[0],
                "parent_id": row[1],
                "filename": row[2],
                "subject": row[3],
                "topic": row[4],
                "chunk_count": row[5],
                "status": row[6],
                "created_at": row[7]
            }
        )

    return {
        "count": len(documents),
        "documents": documents
    }


@router.put("/{document_id}/status/{status}")
def change_document_status(
    document_id: str,
    status: str
):

    update_document_status(
        document_id,
        status
    )

    return {
        "status": "UPDATED",
        "document_id": document_id,
        "new_status": status
    }


@router.delete("/{document_id}")
def remove_document(document_id: str):

    row = get_document(document_id)

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Document not found."
        )

    delete_document_chunks(document_id)
    delete_document_qa_pairs(document_id)
    delete_uploaded_file(document_id)
    delete_document_registry_entry(document_id)

    return {
        "status": "DELETED",
        "document_id": document_id
    }