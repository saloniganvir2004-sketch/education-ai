from fastapi import UploadFile
from fastapi import File
from fastapi import Form

import os
import math
import uuid
import json
import threading
import traceback
import time
import gc

from file_processor import process_file
from utils import chunk_text
from embeddings import generate_embeddings
from vector_store import store_chunks
from subjects import SUBJECTS

from debug_logger import (
    log_ingestion_start,
    log_text_extraction,
    log_chunking,
    log_embedding_progress,
    log_storage,
    log_ingestion_complete,
    log_chunk_metadata,
)


from upload_history_db import (
    add_uploaded_file,
    update_upload_status,
    update_upload_language,
    topic_exists
)

from document_registry import (
    add_document,
    save_document_pages,
)

from subject_topic_registry import add_topic


# Helper to get a unique topic name if one already exists
def get_unique_topic_name(subject: str, topic: str) -> str:
    if not topic_exists(subject, topic):
        return topic

    index = 2
    while topic_exists(subject, f"{topic} ({index})"):
        index += 1

    return f"{topic} ({index})"


UPLOAD_DIR = "../uploads"


MAX_EMBEDDING_CHARS = 3500

SUPPORTED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "jpg",
    "jpeg",
    "png",
    "mp3",
    "wav",
    "mp4"
}


async def save_uploaded_file(
    file: UploadFile = File(...)
):

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    unique_filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        content = await file.read()

        buffer.write(content)

    return file_path


def split_large_chunk(
    chunk: str,
    max_size: int = MAX_EMBEDDING_CHARS
):

    if len(chunk) <= max_size:
        return [chunk]

    sub_chunks = []

    start = 0

    while start < len(chunk):

        end = min(
            start + max_size,
            len(chunk)
        )

        sub_chunk = chunk[start:end].strip()

        if sub_chunk:

            sub_chunks.append(
                sub_chunk
            )

        start = end

    return sub_chunks


def process_file_background(
    file_path,
    file_name,
    parent_id,
    document_id,
    subject,
    topic
):
    pipeline_start = time.perf_counter()
    process_start = 0
    chunking_start = 0
    embedding_start = 0
    store_start = 0

    print(
        "BACKGROUND THREAD STARTED"
    )
    log_ingestion_start(
        filename=file_name,
        subject=subject,
        topic=topic,
        document_id=document_id,
    )

    print(
        "UPLOAD ID:",
        parent_id
    )

    try:

        print(
            "CALLING PROCESS_FILE"
        )

        process_start = time.perf_counter()

        result = process_file(
            file_path
        )

        print(
            "PROCESS FILE TIME:",
            round(
                time.perf_counter() - process_start,
                3
            ),
            "seconds"
        )

        print(
            "PROCESS_FILE RETURNED"
        )

        if not result:

            update_upload_status(
                parent_id,
                "FAILED"
            )

            return

        if not isinstance(
            result,
            dict
        ):

            update_upload_status(
                parent_id,
                "FAILED"
            )

            return

        extracted_text = result.get(
            "text",
            ""
        )

        document_language = result.get(
            "language",
            "english"
        )
        pages = result.get("pages", [])

        text = extracted_text.strip()
        normalized_text = text.replace("\r\n", "\n")
        log_text_extraction(
            characters=len(text),
            language=document_language,
        )

        print(
            "DOCUMENT LANGUAGE:",
            document_language
        )

        update_upload_language(
            parent_id,
            document_language
        )

        if not text:

            update_upload_status(
                parent_id,
                "FAILED"
            )

            return

        if len(text) < 20:

            update_upload_status(
                parent_id,
                "FAILED"
            )

            return

        print(
            "STARTING CHUNKING"
        )

        chunking_start = time.perf_counter()

        chunk_records = chunk_text(
            text
        )

        print(
            "RAW CHUNKS:",
            len(chunk_records)
        )

        safe_chunk_records = []
        for record in chunk_records:
            chunk_text_val = record["text"]
            start_char = record["start_char"]
            end_char = record["end_char"]
            if not chunk_text_val:
                continue
            chunk_text_val = chunk_text_val.strip()
            if len(chunk_text_val) <= 50:
                continue
            sub_offset = 0
            for safe_chunk in split_large_chunk(chunk_text_val):
                safe_chunk = safe_chunk.strip()
                if not safe_chunk:
                    continue
                sub_start = start_char + sub_offset
                sub_end = sub_start + len(safe_chunk)
                safe_chunk_records.append({
                    "text": safe_chunk,
                    "start_char": sub_start,
                    "end_char": sub_end,
                })
                sub_offset += len(safe_chunk)

        safe_chunks = [r["text"] for r in safe_chunk_records]

        print(
            "CHUNKING TIME:",
            round(
                time.perf_counter() - chunking_start,
                3
            ),
            "seconds"
        )

        total_chunks = len(
            safe_chunks
        )
        log_chunking(safe_chunks)

        print(
            "TOTAL CHUNKS:",
            total_chunks
        )

        if not safe_chunks:
            update_upload_status(
                parent_id,
                "FAILED"
            )
            return

        print(
            "STARTING EMBEDDINGS"
        )

        embedding_start = time.perf_counter()

        embeddings = generate_embeddings(
            safe_chunks
        )
        for index in range(1, len(embeddings) + 1):
            log_embedding_progress(index, len(embeddings))
        valid_pairs = [
            (record, embedding)
            for record, embedding in zip(safe_chunk_records, embeddings)
            if embedding is not None
        ]
        safe_chunk_records = [p[0] for p in valid_pairs]
        safe_chunks = [r["text"] for r in safe_chunk_records]
        embeddings = [p[1] for p in valid_pairs]

        if not valid_pairs:
            update_upload_status(
                parent_id,
                "FAILED"
            )
            return

        total_chunks = len(safe_chunks)

        print(
            "EMBEDDING TIME:",
            round(
                time.perf_counter() - embedding_start,
                3
            ),
            "seconds"
        )

        print(
            "EMBEDDINGS GENERATED"
        )

        print(
            "TOTAL EMBEDDINGS:",
            len(embeddings)
        )

        if len(embeddings) != len(safe_chunks):
            update_upload_status(
                parent_id,
                "FAILED"
            )
            return

        # Helper to get page span for a chunk using chunk record char positions
        def get_chunk_page(index):
            if not pages or total_chunks == 0:
                return None, None, None
            chunk_start = safe_chunk_records[index]["start_char"]
            chunk_end = safe_chunk_records[index]["end_char"]
            # Use pages metadata to find overlapping pages
            page_start = None
            page_end = None
            for p in pages:
                start_char = p.get("start_char", 0)
                end_char = p.get("end_char", 0)
                page_num = p.get("page")
                # Overlap if any part of chunk is within the page range (explicit interval overlap)
                if page_start is None and max(chunk_start, start_char) < min(chunk_end, end_char):
                    page_start = page_num
                if max(chunk_start, start_char) < min(chunk_end, end_char):
                    page_end = page_num
            # If not found, fall back to first/last page
            if page_start is None and pages:
                page_start = pages[0].get("page")
            if page_end is None and pages:
                page_end = pages[-1].get("page")
            return page_start, page_start, page_end

        chunk_embeddings = [
            {
                "text": chunk,
                "embedding": embedding,
                "source": file_path,
                "file_name": file_name,
                "chunk_id": str(
                    uuid.uuid4()
                ),
                "parent_id": parent_id,
                "document_id": document_id,
                "subject": subject,
                "topic": topic,
                "chunk_index": index,
                "total_chunks": total_chunks,
                "language": document_language,
                **dict(zip(
                    ["page", "page_start", "page_end"],
                    get_chunk_page(index - 1)
                )),
                "chunk_source": "USER"
            }
            for index, (
                chunk,
                embedding
            ) in enumerate(
                zip(
                    safe_chunks,
                    embeddings
                ),
                start=1
            )
        ]

        print(
            "CHUNK EMBEDDINGS:",
            len(chunk_embeddings)
        )

        processing_steps = [
            f"Text extracted: {len(text)} characters",
            f"Split into {total_chunks} chunks",
            f"Generated {len(embeddings)} embeddings",
            f"Stored {len(chunk_embeddings)} chunks in vector database",
            f"Tagged: subject={subject}, topic={topic}"
        ]

        store_start = time.perf_counter()

        log_chunk_metadata(chunk_embeddings)
        # Store vector embeddings in ChromaDB/vector store.
        store_chunks(
            "education_chunks",
            chunk_embeddings
        )
        # Verify vector store write completed before registry updates.
        log_storage(
            chunk_count=total_chunks,
            subject=subject,
            topic=topic,
        )
        # Register document metadata before completing ingestion.
        add_document(
            document_id=document_id,
            parent_id=parent_id,
            filename=file_name,
            subject=subject,
            topic=topic,
            chunk_count=total_chunks
        )
        if pages:
            # Document pages successfully persisted for backend page APIs.
            save_document_pages(
                document_id=document_id,
                pages=[
                    {
                        "page_number": page.get("page"),
                        "page_text": page.get("text", ""),
                        "page_summary": "",
                    }
                    for page in pages
                ],
            )
            if pages:
                print(f"Persisted {len(pages)} document pages.")
        add_topic(subject, topic)

        log_ingestion_complete()

        total_time = round(
            time.perf_counter() - pipeline_start,
            3
        )

        print()
        print("=" * 60)
        print("INGESTION SUMMARY")
        print("=" * 60)
        print(f"File        : {file_name}")
        print(f"Subject     : {subject}")
        print(f"Topic       : {topic}")
        print(f"Characters  : {len(text)}")
        print(f"Chunks      : {total_chunks}")
        print(f"Embeddings  : {len(embeddings)}")
        print(f"Stored      : {total_chunks}")
        print(f"Extraction  : {round(chunking_start - process_start, 3)} sec")
        print(f"Chunking    : {round(embedding_start - chunking_start, 3)} sec")
        print(f"Embeddings  : {round(store_start - embedding_start, 3)} sec")
        print(f"Storage     : {round(time.perf_counter() - store_start, 3)} sec")
        print(f"Total Time  : {total_time} sec")
        print("=" * 60)
        print()

        del embeddings
        del safe_chunks
        del chunk_embeddings
        del extracted_text
        gc.collect()

        print(
            "UPLOAD COMPLETED"
        )

        update_upload_status(
            parent_id,
            "COMPLETED"
        )

        return {
            "subject": subject,
            "topic": topic,
            "filename": file_name,
            "chunk_count": total_chunks,
            "status": "ACTIVE",
            "processing_steps": processing_steps,
            "ingestion_summary": {
                "subject": subject,
                "topic": topic,
                "chunks_created": total_chunks,
                "processing_steps": processing_steps,
            }
        }

    except Exception as e:

        print(
            "PROCESS FILE ERROR:",
            repr(e)
        )

        traceback.print_exc()

        update_upload_status(
            parent_id,
            "FAILED"
        )

    finally:

        print(
            "TOTAL PIPELINE TIME:",
            round(
                time.perf_counter() - pipeline_start,
                3
            ),
            "seconds"
        )


async def process_uploaded_file(
    file: UploadFile = File(...),
    subject: str = Form(""),
    topic: str = Form(""),
    keep_both: bool = Form(False)
):

    subject = (subject or "").strip()
    if not subject:
        return {
            "status": "FAILED",
            "message": "Subject is required."
        }
    if subject not in SUBJECTS:
        return {
            "status": "FAILED",
            "message": f"Invalid subject '{subject}'.",
            "allowed_subjects": SUBJECTS
        }

    topic = (topic or "").strip()
    if not topic:
        topic = os.path.splitext(file.filename)[0].strip()
    if keep_both:
        topic = get_unique_topic_name(subject, topic)
    if "." not in file.filename:
        return {
            "status": "FAILED",
            "message": "Invalid file name."
        }
    extension = file.filename.rsplit(".", 1)[-1].lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return {
            "status": "FAILED",
            "message": "Unsupported file type.",
            "supported_formats": sorted(SUPPORTED_EXTENSIONS)
        }

    if not file.filename or not file.filename.strip():
        return {
            "status": "FAILED",
            "message": "No file selected."
        }

    content = await file.read()

    MAX_UPLOAD_SIZE = 100 * 1024 * 1024

    if len(content) > MAX_UPLOAD_SIZE:
        return {
            "status": "FAILED",
            "message": "File exceeds 100 MB limit."
        }

    if not content:
        return {
            "status": "FAILED",
            "message": "Uploaded file is empty."
        }

    await file.seek(0)

    file_path = await save_uploaded_file(
        file
    )

    parent_id = str(
        uuid.uuid4()
    )

    document_id = str(
        uuid.uuid4()
    )

    add_uploaded_file(
        filename=file.filename,
        file_path=file_path,
        file_type=file.filename.split(".")[-1].lower(),
        parent_id=parent_id,
        document_id=document_id,
        subject=subject,
        topic=topic,
        status="PROCESSING"
    )

    thread = threading.Thread(
        target=process_file_background,
        args=(
            file_path,
            file.filename,
            parent_id,
            document_id,
            subject,
            topic
        ),
        daemon=True
    )

    thread.start()

    return {
        "status": "PROCESSING",
        "subject": subject,
        "topic": topic,
        "filename": file.filename,
        "parent_id": parent_id,
        "document_id": document_id,
        "chunk_count": 0,
        "uploaded_at": None,
        "ingestion_summary": {
            "subject": subject,
            "topic": topic,
            "chunks_created": 0,
            "processing_steps": []
        }
    }