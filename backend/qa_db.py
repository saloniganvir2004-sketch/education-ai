from pgvector.psycopg2 import register_vector
import time

from database import get_db_connection
from embeddings import generate_embedding

from upload_history_db import (
    get_latest_document,
    get_latest_uploaded_file
)

from cache import (
    get_cached_answer,
    set_cached_answer
)
QA_MATCH_THRESHOLD = 0.82
QA_DUPLICATE_THRESHOLD = 0.99

QUESTION_EMBEDDING_CACHE = {}

# Lightweight schema migration helper for qa_pairs extra metadata columns
def ensure_qa_metadata_columns():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS document_id TEXT")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS subject TEXT")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS topic TEXT")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS intent TEXT")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS qa_source TEXT DEFAULT 'USER'")
        # Add new metadata columns if not exist
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS user_id TEXT")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'RAG'")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        cursor.execute("ALTER TABLE qa_pairs ADD COLUMN IF NOT EXISTS editable BOOLEAN DEFAULT TRUE")
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def add_qa_pair(
    question,
    answer,
    subject_id=None,
    topic_id=None,
    subtopic_id=None,
    document_id=None,
    subject=None,
    topic=None,
    intent=None,
    qa_source="USER",
    user_id=None,
    source="RAG",
    verified=False
):
    ensure_qa_metadata_columns()
    latest_document = get_latest_document()

    if latest_document:
        document_id = document_id or latest_document.get("document_id")
        subject = subject or latest_document.get("subject")
        topic = topic or latest_document.get("topic")

    if not latest_document:
        return

    parent_id = latest_document["parent_id"]

    connection = get_db_connection()

    register_vector(
        connection
    )

    cursor = connection.cursor()

    try:

        if not answer:
            return

        normalized_answer = answer.strip().lower()

        if normalized_answer in {
            "information not found in the provided content.",
            "no content found.",
            "information not found",
            ""
        }:
            return

        if question in QUESTION_EMBEDDING_CACHE:
            print(
                "QUESTION EMBEDDING CACHE HIT"
            )
            question_embedding = QUESTION_EMBEDDING_CACHE[
                question
            ]
        else:
            question_embedding = generate_embedding(
                question
            )
            QUESTION_EMBEDDING_CACHE[
                question
            ] = question_embedding

        if question_embedding is None:
            return

        # Reserved for upcoming metadata persistence.
        _ = (document_id, subject, topic, intent, qa_source)

        cursor.execute(
            """
            SELECT
                question,
                answer,
                1 - (
                    embedding <=> %s::vector
                ) AS similarity
            FROM qa_embeddings
            WHERE parent_id=%s
            ORDER BY embedding <=> %s::vector
            LIMIT 1
            """,
            (
                question_embedding,
                parent_id,
                question_embedding
            )
        )

        existing = cursor.fetchone()

        if existing:

            similarity = float(
                existing[2]
            )

            if similarity >= QA_DUPLICATE_THRESHOLD:

                cursor.close()
                connection.close()

                return

        cursor.execute(
            """
            INSERT INTO qa_pairs
            (
                question,
                answer,
                subject_id,
                topic_id,
                subtopic_id,
                parent_id,
                document_id,
                subject,
                topic,
                intent,
                qa_source,
                user_id,
                source,
                verified
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                question,
                answer,
                subject_id,
                topic_id,
                subtopic_id,
                parent_id,
                document_id,
                subject,
                topic,
                intent,
                qa_source,
                user_id,
                source,
                verified
            )
        )

        cursor.execute(
            """
            INSERT INTO qa_embeddings
            (
                question,
                answer,
                embedding,
                parent_id
            )
            VALUES
            (%s,%s,%s,%s)
            """,
            (
                question,
                answer,
                question_embedding,
                parent_id
            )
        )

        connection.commit()

    except Exception as e:

        print(
            "QA STORE ERROR:",
            e
        )

        connection.rollback()

    finally:

        cursor.close()
        connection.close()


def get_similar_qa_answer(
    question,
    user_id=None
):
    start = time.perf_counter()

    latest_document = get_latest_document()
    document_id = latest_document.get("document_id") if latest_document else None

    if not latest_document:
        print(
            "QA SEARCH TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return None

    parent_id = latest_document["parent_id"]

    uploaded_file = get_latest_uploaded_file()

    if not uploaded_file:
        print(
            "QA SEARCH TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return None

    cached_answer = get_cached_answer(
        question,
        user_id=user_id,
        document_id=document_id,
    )

    if cached_answer:

        print(
            "QA CACHE HIT"
        )

        print(
            "QA SEARCH TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return cached_answer

    connection = get_db_connection()

    register_vector(
        connection
    )

    cursor = connection.cursor()

    try:

        if question in QUESTION_EMBEDDING_CACHE:
            print(
                "QUESTION EMBEDDING CACHE HIT"
            )
            embedding = QUESTION_EMBEDDING_CACHE[
                question
            ]
        else:
            embedding = generate_embedding(
                question
            )
            QUESTION_EMBEDDING_CACHE[
                question
            ] = embedding

        if embedding is None:
            print("QA SEARCH TIME:", round(time.perf_counter() - start, 3), "seconds")
            return None

        cursor.execute(
            """
            SELECT
                question,
                answer,
                1 - (
                    embedding <=> %s::vector
                ) AS similarity
            FROM qa_embeddings
            WHERE parent_id=%s
            ORDER BY embedding <=> %s::vector
            LIMIT 10
            """,
            (
                embedding,
                parent_id,
                embedding
            )
        )

        records = cursor.fetchall()

        if not records:

            cursor.close()
            connection.close()

            print(
                "QA SEARCH TIME:",
                round(
                    time.perf_counter() - start,
                    3
                ),
                "seconds"
            )

            return None

        best_record = None

        best_similarity = 0.0

        for record in records:

            similarity = float(
                record[2]
            )

            if similarity >= 0.97:

                matched_question = record[0]

                answer = record[1]

                set_cached_answer(
                    question,
                    answer,
                    user_id=user_id,
                    document_id=document_id,
                )

                set_cached_answer(
                    matched_question,
                    answer,
                    user_id=user_id,
                    document_id=document_id,
                )

                print(
                    "BEST QA SIMILARITY:",
                    similarity
                )

                cursor.close()
                connection.close()

                print(
                    "QA SEARCH TIME:",
                    round(
                        time.perf_counter() - start,
                        3
                    ),
                    "seconds"
                )

                return answer

            if (
                similarity >= QA_MATCH_THRESHOLD
                and similarity > best_similarity
            ):

                best_similarity = similarity

                best_record = record

        if not best_record:

            cursor.close()
            connection.close()

            print(
                "QA SEARCH TIME:",
                round(
                    time.perf_counter() - start,
                    3
                ),
                "seconds"
            )

            return None

        matched_question = best_record[0]

        answer = best_record[1]

        set_cached_answer(
            question,
            answer,
            user_id=user_id,
            document_id=document_id,
        )

        set_cached_answer(
            matched_question,
            answer,
            user_id=user_id,
            document_id=document_id,
        )

        print(
            "BEST QA SIMILARITY:",
            best_similarity
        )

        cursor.close()
        connection.close()

        print(
            "QA SEARCH TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return answer

    except Exception as e:

        print(
            "QA SEARCH ERROR:",
            e
        )

    finally:

        cursor.close()
        connection.close()

    print(
        "QA SEARCH TIME:",
        round(
            time.perf_counter() - start,
            3
        ),
        "seconds"
    )

    return None



def get_all_qa_pairs():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            subject,
            topic,
            document_id,
            qa_source,
            updated_at
        FROM qa_pairs
        ORDER BY id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return records


# New helper function to fetch a QA pair by id
def get_qa_pair(qa_id):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            subject,
            topic,
            document_id,
            verified,
            created_at,
            updated_at
        FROM qa_pairs
        WHERE id=%s
        LIMIT 1
        """,
        (qa_id,)
    )

    record = cursor.fetchone()

    cursor.close()
    connection.close()

    return record


def get_qa_by_question(
    question
):

    latest_document = get_latest_document()

    if not latest_document:
        return None

    parent_id = latest_document["parent_id"]

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            parent_id
        FROM qa_pairs
        WHERE LOWER(question)=LOWER(%s)
        AND parent_id=%s
        LIMIT 1
        """,
        (
            question,
            parent_id
        )
    )

    record = cursor.fetchone()

    cursor.close()

    connection.close()

    return record


def update_qa_pair(
    qa_id,
    question,
    answer,
    subject=None,
    topic=None,
    verified=None,
):

    connection = get_db_connection()

    register_vector(connection)

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT
                question,
                parent_id
            FROM qa_pairs
            WHERE id=%s
            """,
            (
                qa_id,
            )
        )

        record = cursor.fetchone()

        if not record:
            return

        old_question = record[0]
        parent_id = record[1]

        cursor.execute(
            """
            DELETE FROM qa_embeddings
            WHERE question=%s
            AND parent_id=%s
            """,
            (
                old_question,
                parent_id
            )
        )

        new_embedding = generate_embedding(question)

        if new_embedding is None:
            return

        cursor.execute(
            """
            UPDATE qa_pairs
            SET
                question=%s,
                answer=%s,
                subject=COALESCE(%s, subject),
                topic=COALESCE(%s, topic),
                verified=COALESCE(%s, verified),
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (
                question,
                answer,
                subject,
                topic,
                verified,
                qa_id,
            )
        )

        cursor.execute(
            """
            INSERT INTO qa_embeddings
            (
                question,
                answer,
                embedding,
                parent_id
            )
            VALUES
            (%s,%s,%s,%s)
            """,
            (
                question,
                answer,
                new_embedding,
                parent_id
            )
        )

        connection.commit()

    except Exception as e:

        print(
            "QA UPDATE ERROR:",
            e
        )

        connection.rollback()

    finally:

        cursor.close()

        connection.close()


# Helper function to update the verification status of a QA pair
def update_qa_verification(qa_id, verified):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            UPDATE qa_pairs
            SET
                verified=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=%s
            """,
            (
                verified,
                qa_id,
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception as e:
        print("QA VERIFY ERROR:", e)
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()

def delete_qa_pair(
    qa_id
):

    connection = get_db_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            SELECT question
            FROM qa_pairs
            WHERE id=%s
            """,
            (
                qa_id,
            )
        )

        record = cursor.fetchone()

        if record:

            cursor.execute(
                """
                DELETE FROM qa_embeddings
                WHERE question=%s
                """,
                (
                    record[0],
                )
            )

        cursor.execute(
            """
            DELETE FROM qa_pairs
            WHERE id=%s
            """,
            (
                qa_id,
            )
        )
        deleted_rows = cursor.rowcount

        connection.commit()
        return deleted_rows > 0

    except Exception as e:

        print(
            "QA DELETE ERROR:",
            e
        )

        connection.rollback()
        return False

    finally:

        cursor.close()

        connection.close()

    return False


# Helper function to delete all QA pairs and embeddings for a given document
def delete_document_qa_pairs(document_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM qa_embeddings
            WHERE parent_id IN (
                SELECT parent_id
                FROM document_registry
                WHERE document_id=%s
            )
            """,
            (document_id,)
        )

        cursor.execute(
            """
            DELETE FROM qa_pairs
            WHERE parent_id IN (
                SELECT parent_id
                FROM document_registry
                WHERE document_id=%s
            )
            AND qa_source='USER'
            """,
            (document_id,)
        )
        deleted_pairs = cursor.rowcount

        connection.commit()

        return deleted_pairs

    except Exception as e:

        print(
            "QA DOCUMENT DELETE ERROR:",
            e
        )

        connection.rollback()

        return 0

    finally:

        cursor.close()
        connection.close()


def search_qa_pairs(
    search_text
):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            subject,
            topic,
            document_id,
            verified,
            updated_at
        FROM qa_pairs
        WHERE
            question ILIKE %s OR
            answer ILIKE %s OR
            COALESCE(subject,'') ILIKE %s OR
            COALESCE(topic,'') ILIKE %s
        ORDER BY verified DESC, updated_at DESC NULLS LAST, id DESC
        """,
        (
            f"%{search_text}%",
            f"%{search_text}%",
            f"%{search_text}%",
            f"%{search_text}%"
        )
    )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records



# Helper function to fetch all unverified QA pairs
def get_unverified_qa_pairs():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            subject,
            topic,
            document_id,
            created_at,
            updated_at,
            verified
        FROM qa_pairs
        WHERE verified = FALSE
        ORDER BY updated_at DESC NULLS LAST, id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records


# Helper function to fetch all verified QA pairs

def get_verified_qa_pairs():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            question,
            answer,
            subject,
            topic,
            document_id,
            created_at,
            updated_at,
            verified
        FROM qa_pairs
        WHERE verified = TRUE
        ORDER BY updated_at DESC NULLS LAST, id DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records


# Helper function to get QA statistics for a given subject
def get_subject_qa_statistics(subject_name):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_qa_pairs,
            COUNT(*) FILTER (WHERE verified = TRUE) AS verified_qa_pairs,
            COUNT(*) FILTER (WHERE verified = FALSE) AS unverified_qa_pairs
        FROM qa_pairs
        WHERE subject = %s
        """,
        (subject_name,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "total_qa_pairs": row[0] or 0,
        "verified_qa_pairs": row[1] or 0,
        "unverified_qa_pairs": row[2] or 0,
    }


# Helper function to sync QA records when a subject is renamed

def update_qa_subject_name(
    old_subject,
    new_subject
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE qa_pairs
            SET
                subject=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE subject=%s
            """,
            (
                new_subject,
                old_subject
            )
        )

        connection.commit()

        return cursor.rowcount

    finally:

        cursor.close()
        connection.close()


# Helper function to sync QA records when a topic is renamed

def update_qa_topic_name(
    subject,
    old_topic,
    new_topic
):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            UPDATE qa_pairs
            SET
                topic=%s,
                updated_at=CURRENT_TIMESTAMP
            WHERE subject=%s
            AND topic=%s
            """,
            (
                new_topic,
                subject,
                old_topic
            )
        )

        connection.commit()

        return cursor.rowcount

    finally:

        cursor.close()
        connection.close()