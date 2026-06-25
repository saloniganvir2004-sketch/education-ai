from fastapi import APIRouter, HTTPException

from pydantic import BaseModel
from document_registry import rename_document_topic, rename_document_subject, get_subject_statistics
from vector_store import rename_topic_metadata, rename_subject_metadata

from subject_topic_registry import (
    get_subjects,
    get_topics,
    add_topic,
    rename_topic,
    rename_subject,
)

from document_registry import (
    get_subject_topics,
    get_subject_documents,
)

from qa_db import (
    get_subject_qa_statistics,
    update_qa_subject_name,
    update_qa_topic_name,
)

router = APIRouter(
    prefix="/subjects",
    tags=["Subjects"],
)


@router.get("")
def list_subjects():
    """
    Returns all available subjects.
    """
    subjects = get_subjects()
    return {
        "count": len(subjects),
        "subjects": subjects
    }


# New endpoint: GET /subjects/{subject_name}
from fastapi import Path

@router.get("/{subject_name}")
def get_subject_details(subject_name: str = Path(..., description="The name of the subject")):
    """
    Get details about a subject and its topics.
    """
    subjects = get_subjects()
    if subject_name not in subjects:
        raise HTTPException(status_code=404, detail="Subject not found.")
    topics_rows = get_subject_topics(subject_name)
    topic_names = [row[0] for row in topics_rows]

    doc_stats = get_subject_statistics(subject_name)
    qa_stats = get_subject_qa_statistics(subject_name)

    documents_rows = get_subject_documents(subject_name)

    documents = [
        {
            "document_id": row[0],
            "filename": row[1],
            "subject": row[2],
            "topic": row[3],
            "language": row[4],
            "upload_time": row[5],
            "status": row[6],
            "page_count": row[7],
        }
        for row in documents_rows
    ]

    return {
        "subject": subject_name,
        "topic_count": len(topic_names),
        "topics": topic_names,
        "documents": documents,
        "statistics": {
            "source": "consolidated_subject_view",
            "total_documents": doc_stats.get("total_documents", 0),
            "total_topics": doc_stats.get("total_topics", 0),
            "total_chunks": doc_stats.get("total_chunks", 0),
            "total_qa_pairs": qa_stats.get("total_qa_pairs", 0),
            "verified_qa_pairs": qa_stats.get("verified_qa_pairs", 0),
            "unverified_qa_pairs": qa_stats.get("unverified_qa_pairs", 0)
        }
    }

# Legacy endpoint retained for backward compatibility.
# Topics are also available through GET /subjects/{subject_name}
@router.get("/{subject_name}/topics")
def list_topics(subject_name: str):
    rows = get_subject_topics(subject_name)

    topics = [
        {
            "topic": row[0],
            "chunk_count": row[1],
            "uploaded_at": row[2],
            "status": row[3],
        }
        for row in rows
    ]

    return {
        "subject": subject_name,
        "topics": topics,
    }


# Legacy endpoint retained for backward compatibility.
# Documents are also available through GET /subjects/{subject_name}
@router.get("/{subject_name}/documents")
def list_subject_documents(subject_name: str):
    """
    Returns all uploaded documents for a subject.
    """

    if subject_name not in get_subjects():
        raise HTTPException(
            status_code=404,
            detail="Subject not found.",
        )

    rows = get_subject_documents(subject_name)

    documents = [
        {
            "document_id": row[0],
            "filename": row[1],
            "subject": row[2],
            "topic": row[3],
            "language": row[4],
            "upload_time": row[5],
            "status": row[6],
            "page_count": row[7],
        }
        for row in rows
    ]

    return {
        "subject": subject_name,
        "document_count": len(documents),
        "documents": documents,
    }
# Legacy endpoint retained for backward compatibility.
# Statistics are also available through GET /subjects/{subject_name}
@router.get("/{subject_name}/statistics")
def get_subject_statistics_endpoint(subject_name: str):
    """Return statistics for a subject."""

    if subject_name not in get_subjects():
        raise HTTPException(status_code=404, detail="Subject not found.")

    doc_stats = get_subject_statistics(subject_name)
    qa_stats = get_subject_qa_statistics(subject_name)

    return {
        "subject": subject_name,
        "total_documents": doc_stats.get("total_documents", 0),
        "total_topics": doc_stats.get("total_topics", 0),
        "total_chunks": doc_stats.get("total_chunks", 0),
        "total_qa_pairs": qa_stats.get("total_qa_pairs", 0),
        "verified_qa_pairs": qa_stats.get("verified_qa_pairs", 0),
        "unverified_qa_pairs": qa_stats.get("unverified_qa_pairs", 0),
    }


@router.post("/{subject_name}/topics")
def create_topic(subject_name: str, topic: str):
    """
    Add a new topic to a subject.
    """
    add_topic(subject_name, topic)

    return {
        "status": "success",
        "subject": subject_name,
        "topic": topic,
        "topics": get_topics(subject_name),
    }



# --- Topic rename request model ---
class TopicRenameRequest(BaseModel):
    subject: str
    old_topic: str
    new_topic: str


@router.patch("/rename-topic")
def update_topic_name(payload: TopicRenameRequest):
    """
    Rename an existing topic.
    """
    if payload.old_topic not in get_topics(payload.subject):
        raise HTTPException(
            status_code=404,
            detail="Topic not found.",
        )

    rename_topic(payload.subject, payload.old_topic, payload.new_topic)
    rename_document_topic(payload.subject, payload.old_topic, payload.new_topic)
    rename_topic_metadata(payload.subject, payload.old_topic, payload.new_topic)
    update_qa_topic_name(
        payload.subject,
        payload.old_topic,
        payload.new_topic,
    )

    return {
        "status": "success",
        "subject": payload.subject,
        "topic": payload.new_topic,
        "topics": get_topics(payload.subject)
    }


@router.patch("/rename-subject")
def update_subject_name(
    old_subject: str,
    new_subject: str,
):
    """
    Rename an existing subject.
    """
    if old_subject not in get_subjects():
        raise HTTPException(
            status_code=404,
            detail="Subject not found.",
        )

    rename_subject(
        old_subject,
        new_subject,
    )
    rename_document_subject(old_subject, new_subject)
    rename_subject_metadata(old_subject, new_subject)
    update_qa_subject_name(
        old_subject,
        new_subject,
    )

    return {
        "status": "success",
        "subject": new_subject,
        "subjects": get_subjects(),
    }