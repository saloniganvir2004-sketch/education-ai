from pgvector.psycopg2 import register_vector
import psycopg2
from psycopg2.extras import execute_batch
import hashlib
import gc
import time

from config import settings


EMBEDDING_DIMENSION = 1536
TABLE_INITIALIZED = False


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


def create_embeddings_table():

    conn = get_connection()

    cur = conn.cursor()
    try:
        cur.execute(
            f"""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id BIGSERIAL PRIMARY KEY,
                text TEXT,
                source TEXT,
                file_name TEXT,
                chunk_id TEXT,
                parent_id TEXT,
                document_id TEXT,
                subject TEXT,
                topic TEXT,
                chunk_index INTEGER,
                total_chunks INTEGER,
                page INTEGER,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                language VARCHAR(50) DEFAULT 'english',
                embedding VECTOR({EMBEDDING_DIMENSION})
            );
            """
        )
        conn.commit()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS language VARCHAR(50)
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS document_id TEXT
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS subject TEXT
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS topic TEXT
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS page INTEGER
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS page_start INTEGER
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS page_end INTEGER
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                ALTER TABLE document_chunks
                ADD COLUMN IF NOT EXISTS chunk_source TEXT DEFAULT 'USER'
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                document_chunks_unique_text_idx
                ON document_chunks
                (
                    parent_id,
                    md5(text)
                )
                """
            )
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id)")
            conn.commit()
        except Exception:
            conn.rollback()

        try:
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_subject_topic ON document_chunks(subject, topic)")
            conn.commit()
        except Exception:
            conn.rollback()
    finally:
        cur.close()
        conn.close()

    print(
        "document_chunks table ready"
    )


def store_chunks(
    collection_name,
    chunk_embeddings
):
    global TABLE_INITIALIZED

    total_start = time.perf_counter()

    if not TABLE_INITIALIZED:

        table_start = time.perf_counter()

        create_embeddings_table()

        TABLE_INITIALIZED = True

        print(
            "TABLE CHECK TIME:",
            round(
                time.perf_counter() - table_start,
                3
            ),
            "seconds"
        )
    else:

        print(
            "TABLE CHECK TIME:",
            0.0,
            "seconds"
        )

    conn = get_connection()

    cur = conn.cursor()

    seen_chunks = set()

    parent_ids = {
        item.get(
            "parent_id",
            ""
        )
        for item in chunk_embeddings
        if item.get(
            "parent_id",
            ""
        )
    }

    existing_hashes = set()

    if parent_ids:

        cur.execute(
            """
            SELECT
                parent_id,
                md5(lower(regexp_replace(text, '\\s+', ' ', 'g')))
            FROM document_chunks
            WHERE parent_id = ANY(%s)
            """,
            (
                list(parent_ids),
            )
        )

        existing_hashes = {
            (
                parent_id,
                hash_value
            )
            for parent_id, hash_value in cur.fetchall()
        }

    input_count = len(
        chunk_embeddings
    )

    duplicate_count = 0

    database_duplicate_count = 0

    insert_rows = []

    for item in chunk_embeddings:

        text = str(
            item.get(
                "text",
                ""
            )
        ).strip()

        if not text:
            continue

        normalized_text = (
            text.lower()
            .replace("\n", " ")
            .replace("\r", " ")
        )

        normalized_text = " ".join(
            normalized_text.split()
        )

        normalized_hash = hashlib.md5(
            normalized_text.encode()
        ).hexdigest()

        if normalized_hash in seen_chunks:

            print(
                "DUPLICATE CHUNK SKIPPED"
            )

            duplicate_count += 1

            continue

        seen_chunks.add(
            normalized_hash
        )

        parent_id = item.get(
            "parent_id",
            ""
        )

        text_hash = hashlib.md5(
            normalized_text.encode(
                "utf-8"
            )
        ).hexdigest()

        if (
            parent_id,
            text_hash
        ) in existing_hashes:

            print(
                "DATABASE DUPLICATE CHUNK SKIPPED"
            )

            database_duplicate_count += 1

            continue

        if item.get("embedding") is None:

            print(
                "SKIPPING CHUNK: embedding generation failed"
            )

            continue

        insert_rows.append(
            (
                text,
                item.get("source", ""),
                item.get("file_name", ""),
                item.get("chunk_id", ""),
                parent_id,
                item.get("document_id", ""),
                item.get("subject", ""),
                item.get("topic", ""),
                item.get("chunk_index", 0),
                item.get("total_chunks", 0),
                item.get("page", None),
                item.get("page_start", item.get("page", None)),
                item.get("page_end", item.get("page", None)),
                item.get(
                    "language",
                    "english"
                ),
                item.get("chunk_source", "USER"),
                item["embedding"]
            )
        )

    print(
        "TOTAL INPUT CHUNKS:",
        input_count
    )

    print(
        "UNIQUE CHUNKS:",
        input_count - duplicate_count
    )

    print(
        "DATABASE DUPLICATES:",
        database_duplicate_count
    )

    print(
        "NEW CHUNKS:",
        len(insert_rows)
    )

    store_start = time.perf_counter()

    try:
        if insert_rows:

            execute_batch(
                cur,
                """
                INSERT INTO document_chunks
                (
                    text,
                    source,
                    file_name,
                    chunk_id,
                    parent_id,
                    document_id,
                    subject,
                    topic,
                    chunk_index,
                    total_chunks,
                    page,
                    page_start,
                    page_end,
                    language,
                    chunk_source,
                    embedding
                )
                VALUES
                (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s
                )
                """,
                insert_rows,
                page_size=100
            )

        conn.commit()
        print(f"Chunk persistence verified: {len(insert_rows)} chunks committed.")

    except Exception as e:
        print("VECTOR STORE ERROR:")
        print(e)
        conn.rollback()

    finally:
        cur.close()
        conn.close()

    stored_count = len(
        insert_rows
    )

    print(
        "STORE TIME:",
        round(
            time.perf_counter() - store_start,
            3
        ),
        "seconds"
    )

    print(
        "STORED CHUNKS:",
        stored_count
    )

    print(
        f"{stored_count} chunks stored"
    )

    del insert_rows
    del seen_chunks
    del existing_hashes
    gc.collect()

    print(
        "TOTAL VECTOR STORE TIME:",
        round(
            time.perf_counter() - total_start,
            3
        ),
        "seconds"
    )


# Helper function to delete all chunks for a given document_id
def delete_document_chunks(document_id):
    conn = get_connection()
    cur = conn.cursor()
    deleted = 0
    try:
        cur.execute(
            """
            DELETE FROM document_chunks
            WHERE document_id=%s
            AND chunk_source='USER'
            """,
            (document_id,)
        )
        deleted = cur.rowcount
        conn.commit()
    except Exception as e:
        print("VECTOR STORE DELETE ERROR:", e)
        conn.rollback()
        deleted = 0
    finally:
        cur.close()
        conn.close()
    return deleted

# Rename topic for all document_chunks matching subject and old_topic
def rename_topic_metadata(
    subject,
    old_topic,
    new_topic
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE document_chunks
            SET topic=%s
            WHERE subject=%s
              AND topic=%s
            """,
            (
                new_topic,
                subject,
                old_topic,
            )
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

# Rename subject for all document_chunks matching old_subject
def rename_subject_metadata(
    old_subject,
    new_subject
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            """
            UPDATE document_chunks
            SET subject=%s
            WHERE subject=%s
            """,
            (
                new_subject,
                old_subject,
            )
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()