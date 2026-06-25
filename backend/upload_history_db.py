from database import get_db_connection


def create_uploaded_files_table():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(500) NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            file_path TEXT NOT NULL,
            parent_id VARCHAR(255),
            document_id VARCHAR(255),
            subject VARCHAR(255),
            topic VARCHAR(255),
            language VARCHAR(50) DEFAULT 'english',
            uploaded_by INTEGER,
            status VARCHAR(50) DEFAULT 'uploaded',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    try:

        cursor.execute(
            """
            ALTER TABLE uploaded_files
            ADD COLUMN IF NOT EXISTS language VARCHAR(50)
            DEFAULT 'english'
            """
        )
        connection.commit()

    except Exception:
        connection.rollback()

    try:

        cursor.execute(
            """
            ALTER TABLE uploaded_files
            ADD COLUMN IF NOT EXISTS document_id VARCHAR(255)
            """
        )
        connection.commit()

    except Exception:
        connection.rollback()

    try:

        cursor.execute(
            """
            ALTER TABLE uploaded_files
            ADD COLUMN IF NOT EXISTS subject VARCHAR(255)
            """
        )
        connection.commit()

    except Exception:
        connection.rollback()

    try:

        cursor.execute(
            """
            ALTER TABLE uploaded_files
            ADD COLUMN IF NOT EXISTS topic VARCHAR(255)
            """
        )
        connection.commit()

    except Exception:
        connection.rollback()

    connection.commit()

    cursor.close()
    connection.close()


def add_uploaded_file(
    filename,
    file_path,
    file_type,
    parent_id,
    document_id,
    subject,
    topic,
    status="PROCESSED",
    language="english"
):

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO uploaded_files
            (
                filename,
                file_path,
                file_type,
                parent_id,
                document_id,
                subject,
                topic,
                language,
                status
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                filename,
                file_path,
                file_type,
                parent_id,
                document_id,
                subject,
                topic,
                language,
                status
            )
        )
        connection.commit()
    except Exception as e:
        print("UPLOAD HISTORY ERROR:", e)
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def update_upload_status(
    parent_id,
    status
):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE uploaded_files
        SET status=%s
        WHERE parent_id=%s
        """,
        (
            status,
            parent_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def update_upload_language(
    parent_id,
    language
):

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE uploaded_files
        SET language=%s
        WHERE parent_id=%s
        """,
        (
            language,
            parent_id
        )
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_uploaded_files():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_type,
            file_path,
            parent_id,
            document_id,
            subject,
            topic,
            language,
            status,
            uploaded_by,
            created_at
        FROM uploaded_files
        ORDER BY subject ASC, topic ASC, created_at DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()
    connection.close()

    return records


def get_latest_document():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            parent_id,
            document_id,
            subject,
            topic,
            language
        FROM uploaded_files
        WHERE status='COMPLETED'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if not row:
        return None

    print(
        "ACTIVE FILE PARENT:",
        row[0]
    )

    print(
        "ACTIVE DOCUMENT:",
        row[1]
    )

    print(
        "ACTIVE SUBJECT:",
        row[2]
    )

    print(
        "ACTIVE TOPIC:",
        row[3]
    )

    print(
        "ACTIVE FILE LANGUAGE:",
        row[4]
    )

    return {
        "parent_id": row[0],
        "document_id": row[1],
        "subject": row[2],
        "topic": row[3],
        "language": row[4]
    }


def get_latest_uploaded_file():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_type,
            file_path,
            parent_id,
            document_id,
            subject,
            topic,
            language,
            status,
            created_at
        FROM uploaded_files
        WHERE status='COMPLETED'
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if not row:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "file_type": row[2],
        "file_path": row[3],
        "parent_id": row[4],
        "document_id": row[5],
        "subject": row[6],
        "topic": row[7],
        "language": row[8],
        "status": row[9],
        "created_at": row[10]
    }

def get_document_by_id(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            filename,
            file_type,
            file_path,
            parent_id,
            document_id,
            subject,
            topic,
            language,
            status,
            created_at
        FROM uploaded_files
        WHERE document_id=%s
        LIMIT 1
        """,
        (document_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if not row:
        return None

    return {
        "id": row[0],
        "filename": row[1],
        "file_type": row[2],
        "file_path": row[3],
        "parent_id": row[4],
        "document_id": row[5],
        "subject": row[6],
        "topic": row[7],
        "language": row[8],
        "status": row[9],
        "created_at": row[10],
    }

def topic_exists(subject: str, topic: str) -> bool:
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT 1
            FROM uploaded_files
            WHERE LOWER(subject)=LOWER(%s)
              AND LOWER(topic)=LOWER(%s)
            LIMIT 1
            """,
            (subject, topic)
        )
        return cursor.fetchone() is not None
    finally:
        cursor.close()
        connection.close()

def delete_uploaded_file(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM uploaded_files
            WHERE document_id=%s
            """,
            (
                document_id,
            )
        )
        connection.commit()
    except Exception as e:
        print("UPLOAD HISTORY DELETE ERROR:", e)
        connection.rollback()
    finally:
        cursor.close()
        connection.close()

# Backward-compatible alias used by the cascade delete pipeline.
def delete_document_upload_history(document_id):
    """Backward-compatible alias used by the cascade delete pipeline."""
    delete_uploaded_file(document_id)