from fastapi import APIRouter, HTTPException

from qa_db import (
    get_all_qa_pairs,
    get_qa_pair,
    update_qa_pair,
    update_qa_verification,
    delete_qa_pair,
    add_qa_pair,
    search_qa_pairs,
    get_unverified_qa_pairs,
    get_verified_qa_pairs,
)

router = APIRouter()


@router.get("")
def list_qa_pairs(
    query: str | None = None,
    verified: bool | None = None,
):
    """
    Returns all stored QA pairs.
    """
    if query:
        qa_pairs = search_qa_pairs(query)
    elif verified is True:
        qa_pairs = get_verified_qa_pairs()
    elif verified is False:
        qa_pairs = get_unverified_qa_pairs()
    else:
        qa_pairs = get_all_qa_pairs()

    return {
        "count": len(qa_pairs),
        "qa_pairs": qa_pairs,
    }




@router.get("/unverified")
def list_unverified_qa():
    """Return all unverified QA pairs."""

    qa_pairs = get_unverified_qa_pairs()

    return {
        "count": len(qa_pairs),
        "qa_pairs": qa_pairs,
    }

@router.get("/verified")
def list_verified_qa():
    """Return all verified QA pairs."""

    qa_pairs = get_verified_qa_pairs()

    return {
        "count": len(qa_pairs),
        "qa_pairs": qa_pairs,
    }

@router.get("/{qa_id}")
def get_qa(qa_id: int):
    """
    Returns a single QA pair.
    """
    qa = get_qa_pair(qa_id)

    if not qa:
        raise HTTPException(
            status_code=404,
            detail="QA pair not found.",
        )

    return qa


@router.post("")
def create_qa(payload: dict):
    """
    Manually create a QA pair.
    """
    if "question" not in payload or "answer" not in payload:
        raise HTTPException(
            status_code=422,
            detail="Both 'question' and 'answer' are required."
        )

    add_qa_pair(
        question=payload["question"],
        answer=payload["answer"],
        subject=payload.get("subject"),
        topic=payload.get("topic"),
        document_id=payload.get("document_id"),
        user_id=payload.get("user_id"),
        source=payload.get("source", "MANUAL"),
        verified=True,
        qa_source="ADMIN",
    )

    return {
        "message": "QA pair created successfully."
    }


@router.patch("/{qa_id}")
def edit_qa(qa_id: int, payload: dict):
    """
    Edit an existing QA pair.
    """

    updated = update_qa_pair(
        qa_id=qa_id,
        question=payload.get("question"),
        answer=payload.get("answer"),
        subject=payload.get("subject"),
        topic=payload.get("topic"),
        verified=payload.get("verified"),
    )

    if updated is False:
        raise HTTPException(
            status_code=404,
            detail="QA pair not found.",
        )

    return {
        "message": "QA pair updated successfully."
    }


@router.patch("/{qa_id}/verify")
def verify_qa(qa_id: int, payload: dict):
    """Mark a QA pair as verified or unverified."""

    updated = update_qa_verification(
        qa_id=qa_id,
        verified=payload.get("verified", True),
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="QA pair not found.",
        )

    return {
        "message": "QA verification updated successfully.",
        "verified": payload.get("verified", True),
    }


@router.delete("/{qa_id}")
def remove_qa(qa_id: int):
    """
    Delete a QA pair.
    """

    deleted = delete_qa_pair(qa_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="QA pair not found.",
        )

    return {
        "message": "QA pair deleted successfully."
    }