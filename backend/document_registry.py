from database import get_db_connection


def create_document_registry_table():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_registry
        (
            document_id VARCHAR(100) UNIQUE NOT NULL,
            parent_id VARCHAR(100) NOT NULL,
            filename TEXT NOT NULL,
            subject VARCHAR(255) NOT NULL,
            topic VARCHAR(255) NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            status VARCHAR(30) DEFAULT 'ACTIVE',
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    # Upgrade existing databases
    try:
        cursor.execute(
            """
            ALTER TABLE document_registry
            ADD COLUMN IF NOT EXISTS status
            VARCHAR(30) DEFAULT 'ACTIVE'
            """
        )
        connection.commit()
    except Exception:
        connection.rollback()

    try:
        cursor.execute(
            """
            ALTER TABLE document_registry
            ADD COLUMN IF NOT EXISTS uploaded_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )
        connection.commit()
    except Exception:
        connection.rollback()

    cursor.close()
    connection.close()


def add_document(
    document_id,
    parent_id,
    filename,
    subject,
    topic,
    chunk_count
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO document_registry
        (
            document_id,
            parent_id,
            filename,
            subject,
            topic,
            chunk_count
        )
        VALUES
        (%s,%s,%s,%s,%s,%s)
        """,
        (
            document_id,
            parent_id,
            filename,
            subject,
            topic,
            chunk_count
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_documents():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            document_id,
            parent_id,
            filename,
            subject,
            topic,
            chunk_count,
            status,
            uploaded_at
        FROM document_registry
        ORDER BY
            subject ASC,
            topic ASC,
            uploaded_at DESC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def get_document(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            document_id,
            parent_id,
            filename,
            subject,
            topic,
            chunk_count,
            status,
            uploaded_at
        FROM document_registry
        WHERE document_id=%s
        """,
        (
            document_id,
        )
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return row


def get_document_overview(document_id):
    """
    Returns document metadata for the overview endpoint.
    """

    document = get_document(document_id)

    if not document:
        return None

    pages = get_document_pages(document_id)
    chunks = get_document_chunks(document_id)

    return {
        "document_id": document[0],
        "parent_id": document[1],
        "filename": document[2],
        "subject": document[3],
        "topic": document[4],
        "total_chunks": len(chunks),
        "total_pages": len(pages),
        "sample_chunks": [chunk[4][:100] for chunk in chunks[:3]],
        "status": document[6],
        "uploaded_at": document[7],
        "pages": pages,
        "chunks": chunks[:3],
    }


def update_document_status(
    document_id,
    status
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE document_registry
        SET status=%s
        WHERE document_id=%s
        """,
        (
            status,
            document_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


# New function: update_document
def update_document(
    document_id,
    subject=None,
    topic=None,
    status=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    updates = []
    values = []

    if subject is not None:
        updates.append("subject=%s")
        values.append(subject)

    if topic is not None:
        updates.append("topic=%s")
        values.append(topic)

    if status is not None:
        updates.append("status=%s")
        values.append(status)

    if not updates:
        cursor.close()
        connection.close()
        return False

    values.append(document_id)

    cursor.execute(
        f"""
        UPDATE document_registry
        SET {', '.join(updates)}
        WHERE document_id=%s
        """,
        tuple(values)
    )

    connection.commit()

    updated_rows = cursor.rowcount

    cursor.close()
    connection.close()

    return updated_rows > 0

def delete_document(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM document_registry
        WHERE document_id=%s
        """,
        (
            document_id,
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


# Helper function to delete a document_registry entry by document_id
def delete_document_registry_entry(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        DELETE FROM document_registry
        WHERE document_id=%s
        """,
        (document_id,)
    )
    connection.commit()
    cursor.close()
    connection.close()


def get_documents_by_topic(
    subject,
    topic
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            document_id,
            parent_id,
            filename,
            subject,
            topic,
            chunk_count,
            status,
            uploaded_at
        FROM document_registry
        WHERE
            subject=%s
            AND topic=%s
            AND status='ACTIVE'
        ORDER BY uploaded_at DESC
        """,
        (
            subject,
            topic
        )
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def get_subject_topics(subject):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            topic,
            chunk_count,
            uploaded_at,
            status
        FROM document_registry
        WHERE subject=%s
          AND status='ACTIVE'
        ORDER BY topic ASC, uploaded_at DESC
        """,
        (subject,)
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def rename_document_topic(
    subject,
    old_topic,
    new_topic
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE document_registry
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

    connection.commit()

    cursor.close()
    connection.close()

# Add: rename_document_subject
def rename_document_subject(
    old_subject,
    new_subject
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE document_registry
        SET subject=%s
        WHERE subject=%s
        """,
        (
            new_subject,
            old_subject,
        )
    )

    connection.commit()
    cursor.close()
    connection.close()



# Helper function: get_subject_documents
def get_subject_documents(subject):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            document_id,
            filename,
            subject,
            topic,
            'Unknown' AS language,
            uploaded_at,
            status,
            (SELECT COUNT(*) FROM document_pages dp WHERE dp.document_id = document_registry.document_id) AS page_count
        FROM document_registry
        WHERE subject=%s
          AND status='ACTIVE'
        ORDER BY uploaded_at DESC
        """,
        (subject,)
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def get_subject_list():
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT DISTINCT subject
        FROM document_registry
        WHERE status='ACTIVE'
        ORDER BY subject ASC
        """
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return [row[0] for row in rows]


# Helper function: get statistics for a subject
def get_subject_statistics(subject_name):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(DISTINCT document_id) AS total_documents,
            COUNT(DISTINCT topic) AS total_topics,
            COALESCE(SUM(chunk_count), 0) AS total_chunks
        FROM document_registry
        WHERE subject=%s
          AND status='ACTIVE'
        """,
        (subject_name,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "total_documents": row[0] or 0,
        "total_topics": row[1] or 0,
        "total_chunks": row[2] or 0,
    }


# Compatibility wrappers for document routes

def get_all_documents():
    return get_documents()


def get_document_by_id(document_id):
    return get_document(document_id)


def get_document_content(document_id):
    document = get_document(document_id)

    if not document:
        return None

    return {
        "document": document,
        "pages": get_document_pages(document_id),
        "chunks": get_document_chunks(document_id),
    }


# Helper function: get_document_chunks
def get_document_chunks(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                chunk_id,
                NULL AS page_number,
                NULL AS page_start,
                NULL AS page_end,
                text,
                NULL AS embedding_status
            FROM document_chunks
            WHERE document_id=%s
            ORDER BY chunk_id ASC
            """,
            (document_id,)
        )
        rows = cursor.fetchall()
    except Exception:
        connection.rollback()
        cursor.execute(
            """
            SELECT text
            FROM document_chunks
            WHERE document_id=%s
            """,
            (document_id,)
        )
        raw_rows = cursor.fetchall()
        rows = [
            (index + 1, None, None, None, row[0], None)
            for index, row in enumerate(raw_rows)
        ]

    cursor.close()
    connection.close()

    return rows


def get_document_pages(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_pages
        (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(100) NOT NULL,
            page_number INTEGER NOT NULL,
            page_text TEXT,
            page_summary TEXT DEFAULT ''
        )
        """
    )
    connection.commit()

    cursor.execute(
        """
        SELECT
            page_number,
            page_text,
            COALESCE(page_summary, '') AS page_summary
        FROM document_pages
        WHERE document_id=%s
        ORDER BY page_number ASC
        """,
        (document_id,)
    )

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    return rows


def save_document_pages(document_id, pages):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_pages
        (
            id SERIAL PRIMARY KEY,
            document_id VARCHAR(100) NOT NULL,
            FOREIGN KEY (document_id) REFERENCES document_registry(document_id) ON DELETE CASCADE,
            page_number INTEGER NOT NULL,
            page_text TEXT,
            page_summary TEXT DEFAULT ''
        )
        """
    )

    cursor.execute(
        "DELETE FROM document_pages WHERE document_id=%s",
        (document_id,),
    )

    for page in pages:
        cursor.execute(
            """
            INSERT INTO document_pages
            (document_id, page_number, page_text, page_summary)
            VALUES (%s,%s,%s,%s)
            """,
            (
                document_id,
                page["page_number"],
                page["page_text"],
                page.get("page_summary", ""),
            ),
        )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_pages_document_id
        ON document_pages(document_id)
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_document_pages_page_number
        ON document_pages(document_id, page_number)
        """
    )


    connection.commit()
    cursor.close()
    connection.close()


create_document_registry_table()