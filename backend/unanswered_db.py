from database import get_db_connection


def create_unanswered_questions_table():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS unanswered_questions
        (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255),
            question TEXT NOT NULL,
            language VARCHAR(50),
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    try:

        cursor.execute(
            """
            ALTER TABLE unanswered_questions
            ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)
            """
        )

    except Exception as e:

        print(
            "UNANSWERED TABLE ALTER ERROR:",
            e
        )

    try:
        cursor.execute(
            """
            ALTER TABLE unanswered_questions
            ADD COLUMN IF NOT EXISTS document_id TEXT
            """
        )
    except Exception as e:
        print("UNANSWERED TABLE ALTER ERROR:", e)

    connection.commit()

    cursor.close()

    connection.close()


def add_unanswered_question(
    question,
    language,
    reason="Information not found in the provided content.",
    user_id=None,
    document_id=None
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO unanswered_questions
        (
            user_id,
            question,
            language,
            reason,
            document_id
        )
        VALUES
        (%s,%s,%s,%s,%s)
        """,
        (
            user_id,
            question,
            language,
            reason,
            document_id
        )
    )

    connection.commit()

    cursor.close()

    connection.close()


def get_unanswered_questions():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            question,
            language,
            reason,
            created_at
        FROM unanswered_questions
        ORDER BY created_at DESC
        """
    )

    records = cursor.fetchall()

    cursor.close()

    connection.close()

    return records


def get_unanswered_questions_by_user(
    user_id
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            question,
            language,
            reason,
            created_at
        FROM unanswered_questions
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


def delete_unanswered_question(
    question_id
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM unanswered_questions
        WHERE id=%s
        """,
        (
            question_id,
        )
    )

    connection.commit()

    cursor.close()

    connection.close()


def get_unanswered_question(
    question_id
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            user_id,
            question,
            language,
            reason,
            created_at
        FROM unanswered_questions
        WHERE id=%s
        """,
        (
            question_id,
        )
    )

    record = cursor.fetchone()

    cursor.close()

    connection.close()

    return record


def delete_document_unanswered_questions(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            DELETE FROM unanswered_questions
            WHERE document_id=%s
            """,
            (document_id,)
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


create_unanswered_questions_table()