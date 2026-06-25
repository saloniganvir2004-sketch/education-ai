from pgvector.psycopg2 import register_vector
import psycopg2
import time

from embeddings import generate_embedding
from config import settings
from translator import (
    normalize_numbers,
    detect_language
)

from upload_history_db import (
    get_latest_document,
    get_document_by_id,
)

from debug_logger import (
    log_retrieval_start,
    log_cross_topic_search,
    log_ranking,
    log_topic_summary,
    log_search_path,
)


MIN_SCORE_THRESHOLD = 0.20
TOP_K = settings.TOP_K
NEIGHBOR_WINDOW = 0
STOPWORDS = {
    "the",
    "is",
    "are",
    "was",
    "were",
    "a",
    "an",
    "of",
    "to",
    "in",
    "on",
    "for",
    "with",
    "and",
    "or",
    "then",
    "next",
    "after",
    "what",
    "who",
    "why",
    "how",
    "did",
    "does",
    "do",
    "he",
    "she",
    "they",
    "it",
    "this",
    "that",
    "kya",
    "hai",
    "hain",
    "tha",
    "thi",
    "woh",
    "usne",
    "use",
    "uska",
    "uski",
    "uske",
    "phir",
    "fir",
    "baad"
}


def get_meaningful_words(text):
    return {
        word.lower().strip(".,!?;:\"'()[]{}")
        for word in text.split()
        if (
            len(word.lower().strip(".,!?;:\"'()[]{}")) >= 3
            and word.lower().strip(".,!?;:\"'()[]{}") not in STOPWORDS
        )
    }


def get_connection():

    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        dbname=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD
    )

    register_vector(conn)

    return conn


def retrieve_chunks(
    question,
    limit=TOP_K,
    threshold=MIN_SCORE_THRESHOLD,
    document_id=None,
    subject=None
):
    retrieval_start = time.perf_counter()

    print(
        "RETRIEVER QUESTION:",
        question
    )

    print(
        "RETRIEVER LANGUAGE:",
        detect_language(
            question
        )
    )

    normalized_question = normalize_numbers(
        question
    )

    detected_subject = subject

    if not detected_subject:

        lower_question = normalized_question.lower()

        math_keywords = [
            "integer",
            "integers",
            "trigonometry",
            "equation",
            "equations",
            "set",
            "sets",
            "function",
            "functions",
            "algebra",
            "mathematics",
            "math"
        ]

        physics_keywords = [
            "reflection",
            "refraction",
            "light",
            "mirror",
            "lens",
            "human eye",
            "dispersion",
            "physics"
        ]

        if any(keyword in lower_question for keyword in math_keywords):

            detected_subject = "Mathematics"

        elif any(keyword in lower_question for keyword in physics_keywords):

            detected_subject = "Physics"

    if document_id:
        latest_document = get_document_by_id(document_id)
    elif detected_subject:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT document_id, parent_id, subject, topic
            FROM document_registry
            WHERE subject = %s
              AND status = 'ACTIVE'
            ORDER BY uploaded_at DESC
            LIMIT 1
            """,
            (detected_subject,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row:
            latest_document = {
                "document_id": row[0],
                "parent_id": row[1],
                "subject": row[2],
                "topic": row[3]
            }
        else:
            latest_document = get_latest_document()
            if latest_document and detected_subject and latest_document.get("subject") != detected_subject:
                latest_document = None
    else:
        latest_document = get_latest_document()
        if latest_document and detected_subject and latest_document.get("subject") != detected_subject:
            latest_document = None

    if not latest_document:
        print(
            "RETRIEVAL TIME:",
            time.perf_counter() - retrieval_start
        )

        return []

    active_parent_id = latest_document["parent_id"]
    active_document_id = (
        document_id
        if document_id is not None
        else latest_document["document_id"]
    )
    active_subject = latest_document["subject"]

    if detected_subject and active_subject != detected_subject:

        print(
            "SUBJECT CORRECTION:",
            active_subject,
            "->",
            detected_subject
        )

        active_subject = detected_subject
    active_topic = latest_document["topic"]

    retrieval_context = {
        "document_id": active_document_id,
        "subject": active_subject,
        "topic": active_topic,
        "parent_id": active_parent_id
    }

    print("=" * 80)
    print("RETRIEVAL CONTEXT DOCUMENT:", retrieval_context["document_id"])
    print("RETRIEVAL CONTEXT SUBJECT :", retrieval_context["subject"])
    print("RETRIEVAL CONTEXT TOPIC   :", retrieval_context["topic"])
    print("=" * 80)

    retrieval_filter = "document"
    if not active_document_id and active_subject and active_topic:
        retrieval_filter = "subject_topic"

    print(
        "ACTIVE DOCUMENT:",
        active_document_id
    )

    print(
        "ACTIVE SUBJECT:",
        active_subject
    )

    print(
        "ACTIVE TOPIC:",
        active_topic
    )

    log_retrieval_start(
        question=normalized_question,
        subject=active_subject,
        topic=active_topic,
    )

    query_embedding = generate_embedding(
        normalized_question
    )

    if query_embedding is None:

        print(
            "EMBEDDING GENERATION FAILED"
        )

        print(
            "RETRIEVAL TIME:",
            time.perf_counter() - retrieval_start
        )

        return []

    conn = get_connection()

    cur = conn.cursor()

    limit = max(1, int(limit))

    if retrieval_filter == "document":
        cur.execute(
            """
            SELECT
                text, source, file_name, chunk_id, parent_id,
                document_id, subject, topic, chunk_index,
                total_chunks,
                page,
                page_start,
                page_end,
                language,
                1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE document_id=%s
            ORDER BY embedding <=> %s::vector
            LIMIT %s * 3
            """,
            (query_embedding, active_document_id, query_embedding, limit)
        )
    else:
        cur.execute(
            """
            SELECT
                text, source, file_name, chunk_id, parent_id,
                document_id, subject, topic, chunk_index,
                total_chunks,
                page,
                page_start,
                page_end,
                language,
                1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE subject=%s AND topic=%s
            ORDER BY embedding <=> %s::vector
            LIMIT %s * 3
            """,
            (query_embedding, active_subject, active_topic, query_embedding, limit)
        )

    rows = cur.fetchall()

    # Cross-topic retrieval: If not enough rows and subject is set, get from other topics in same subject
    if active_subject:
        cur.execute(
            """
            SELECT
                text, source, file_name, chunk_id, parent_id,
                document_id, subject, topic, chunk_index,
                total_chunks,
                page,
                page_start,
                page_end,
                language,
                1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE subject=%s
              AND topic<>%s
            ORDER BY embedding <=> %s::vector
            LIMIT %s * 2
            """,
            (query_embedding, active_subject, active_topic, query_embedding, limit)
        )
        existing_chunk_ids = {row[3] for row in rows}
        extra_rows = [
            row
            for row in cur.fetchall()
            if row[3] not in existing_chunk_ids
        ]
        rows.extend(extra_rows)
        print("PRIMARY TOPIC ROWS:", len(existing_chunk_ids))
        print("CROSS TOPIC ROWS:", len(extra_rows))

    retrieval_preview = []
    for row in rows:
        retrieval_preview.append({
            "topic": row[7],
            "subject": row[6],
            "page": row[10],
            "score": float(row[14]),
            "document_id": row[5],
        })
    log_cross_topic_search(retrieval_preview)

    if not rows:
        print("RAW ROWS FOUND:", 0)

    try:

        top_vector_score = max(
            (float(row[14]) for row in rows),
            default=0.0
        )

        print(
            "TOP VECTOR SCORE:",
            top_vector_score
        )

        filtered_rows = [row for row in rows if float(row[14]) >= threshold]
        if filtered_rows:
            rows = filtered_rows
        elif question.strip().lower() == "generate questions from uploaded content":
            rows = rows[:limit]

        print(
            "RAW ROWS FOUND:",
            len(rows)
        )

        if not rows:

            print(
                "BEST COMBINED SCORE:",
                0.0
            )
            print(
                "RETRIEVAL TIME:",
                time.perf_counter() - retrieval_start
            )

            return []

        all_chunks = []

        seen_text = set()

        question_words = get_meaningful_words(
            normalized_question
        )

        for row in rows:

            text = str(
                row[0]
            ).strip()

            if not text:
                continue

            document_language = (
                row[13]
                or "english"
            ).lower()

            print(
                "DOCUMENT LANGUAGE:",
                document_language
            )

            score = float(
                row[14]
            )

            selected_topic = retrieval_context.get(
                "topic"
            )

            if (
                selected_topic
                and row[7] == selected_topic
            ):
                score += 0.05

            normalized_text = normalize_numbers(
                text
            )

            text_words = get_meaningful_words(
                normalized_text
            )

            overlap = len(
                question_words.intersection(
                    text_words
                )
            )

            if (
                question.strip().lower() != "generate questions from uploaded content"
                and score < threshold
            ):
                continue

            if text in seen_text:
                continue

            if score >= 0.95 and overlap >= 3:
                all_chunks.append(
                    {
                        "text": text,
                        "score": score,
                        "keyword_overlap": overlap,
                        "combined_score": score,
                        "source": row[1],
                        "file_name": row[2],
                        "chunk_id": row[3],
                        "parent_id": row[4],
                        "document_id": row[5],
                        "subject": row[6],
                        "topic": row[7],
                        "chunk_index": row[8],
                        "total_chunks": row[9],
                        "page": row[10],
                        "page_start": row[11],
                        "page_end": row[12],
                        "language": document_language
                    }
                )

                seen_text.add(
                    text
                )

                continue

            if overlap >= 3:
                combined_score = score * 0.60 + min(overlap, 5) * 0.40
            else:
                combined_score = score * 0.80 + min(overlap, 5) * 0.20

            all_chunks.append(
                {
                    "text": text,
                    "score": score,
                    "keyword_overlap": overlap,
                    "combined_score": combined_score,
                    "source": row[1],
                    "file_name": row[2],
                    "chunk_id": row[3],
                    "parent_id": row[4],
                    "document_id": row[5],
                    "subject": row[6],
                    "topic": row[7],
                    "chunk_index": row[8],
                    "total_chunks": row[9],
                    "page": row[10],
                    "page_start": row[11],
                    "page_end": row[12],
                    "language": document_language
                }
            )

            seen_text.add(
                text
            )

        all_chunks.sort(
            key=lambda x: (
                x["combined_score"],
                x["score"]
            ),
            reverse=True
        )
        log_ranking(all_chunks)
        log_topic_summary(all_chunks)

        best_combined_score = (
            all_chunks[0]["combined_score"]
            if all_chunks
            else 0.0
        )

        print(
            "BEST COMBINED SCORE:",
            best_combined_score
        )

        print(
            "FINAL CHUNKS:",
            len(all_chunks)
        )

        print(
            "RETRIEVAL TIME:",
            time.perf_counter() - retrieval_start
        )

        retrieval_trace = {
            "primary_topic": active_topic,
            "cross_topics": sorted({
                chunk["topic"]
                for chunk in all_chunks
                if chunk.get("topic") and chunk.get("topic") != active_topic
            }),
            "total_chunks_retrieved": len(all_chunks),
            "topics_searched": sorted({
                chunk["topic"]
                for chunk in all_chunks
                if chunk.get("topic")
            })
        }
        log_search_path(
            active_topic,
            retrieval_trace["topics_searched"],
        )
        results = all_chunks[:limit]

        for chunk in results:
            chunk["retrieval_trace"] = retrieval_trace
            chunk["active_document_id"] = retrieval_context["document_id"]
            chunk["active_subject"] = retrieval_context["subject"]
            chunk["active_topic"] = retrieval_context["topic"]
            chunk["active_parent_id"] = retrieval_context["parent_id"]

            # Preserve the actual retrieved chunk metadata
            chunk["retrieved_subject"] = chunk.get("subject")
            chunk["retrieved_topic"] = chunk.get("topic")
            chunk["source_label"] = (
                f"{chunk.get('retrieved_subject', 'Unknown')} > "
                f"{chunk.get('retrieved_topic', 'Unknown')}"
            )

        return results

    finally:
        cur.close()
        conn.close()