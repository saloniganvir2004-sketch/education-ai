import uuid

from database import get_db_connection


TASK_RETENTION_HOURS = 3


def create_tasks_table():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks
        (
            id SERIAL PRIMARY KEY,
            task_id VARCHAR(100) UNIQUE NOT NULL,
            user_id VARCHAR(255),
            conversation_id INTEGER,
            question TEXT,
            answer TEXT,
            language VARCHAR(50),
            status VARCHAR(50),
            source_type VARCHAR(50),
            document_id VARCHAR(100),
            subject VARCHAR(255),
            topic VARCHAR(255),
            confidence FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    try:

        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)
            """
        )

        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS conversation_id INTEGER
            """
        )
        
        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS confidence FLOAT
            """
        )

        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS document_id VARCHAR(100)
            """
        )

        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS subject VARCHAR(255)
            """
        )

        cursor.execute(
            """
            ALTER TABLE tasks
            ADD COLUMN IF NOT EXISTS topic VARCHAR(255)
            """
        )

    except Exception as e:

        print(
            "TASK TABLE ALTER ERROR:",
            e
        )

    connection.commit()

    cursor.close()

    connection.close()


def cleanup_old_tasks():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        f"""
        DELETE FROM tasks
        WHERE updated_at <
        CURRENT_TIMESTAMP -
        INTERVAL '{TASK_RETENTION_HOURS} hours'
        """
    )

    connection.commit()

    cursor.close()

    connection.close()


# Backward-compatible alias for cleanup_old_tasks
def cleanup_expired_tasks():
    """Backward-compatible alias for cleanup_old_tasks."""
    cleanup_old_tasks()


def create_task(
    question,
    language,
    user_id,
    conversation_id,
    source_type="text",
    document_id=None,
    subject=None,
    topic=None
):

    cleanup_old_tasks()

    task_id = str(
        uuid.uuid4()
    )

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO tasks
        (
            task_id,
            user_id,
            conversation_id,
            question,
            language,
            status,
            source_type,
            document_id,
            subject,
            topic
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            task_id,
            user_id,
            conversation_id,
            question,
            language,
            "PROCESSING",
            source_type,
            document_id,
            subject,
            topic
        )
    )

    connection.commit()

    cursor.close()

    connection.close()

    return task_id


def update_task(
    task_id,
    answer="",
    status="COMPLETED",
    confidence=None
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET
            answer=%s,
            status=%s,
            confidence=%s,
            updated_at=CURRENT_TIMESTAMP
        WHERE task_id=%s
        """,
        (
            answer,
            status,
            confidence,
            task_id
        )
    )

    connection.commit()

    cursor.close()

    connection.close()


# Delete all tasks for a given document_id
def delete_document_tasks(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM tasks
            WHERE document_id=%s
            """,
            (document_id,)
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_task(task_id):

    cleanup_old_tasks()
    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            task_id,
            user_id,
            conversation_id,
            question,
            answer,
            language,
            status,
            source_type,
            document_id,
            subject,
            topic,
            confidence,
            created_at,
            updated_at
        FROM tasks
        WHERE task_id=%s
        """,
        (
            task_id,
        )
    )

    record = cursor.fetchone()

    cursor.close()

    connection.close()

    return record


def get_tasks_by_user(
    user_id
):

    cleanup_old_tasks()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            task_id,
            question,
            answer,
            language,
            status,
            source_type,
            document_id,
            subject,
            topic,
            conversation_id,
            created_at,
            updated_at
        FROM tasks
        WHERE user_id=%s
        ORDER BY created_at DESC
        """,
        (
            user_id,
        )
    )

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return records


def get_conversation_tasks(
    conversation_id
):

    cleanup_old_tasks()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            task_id,
            question,
            answer,
            language,
            status,
            source_type,
            document_id,
            subject,
            topic,
            created_at,
            updated_at
        FROM tasks
        WHERE conversation_id=%s
        ORDER BY created_at DESC
        """,
        (
            conversation_id,
        )
    )

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return records


def get_all_tasks():

    cleanup_old_tasks()

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            task_id,
            user_id,
            conversation_id,
            question,
            answer,
            language,
            status,
            source_type,
            document_id,
            subject,
            topic,
            confidence,
            created_at,
            updated_at
        FROM tasks
        ORDER BY created_at DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return records


create_tasks_table()
