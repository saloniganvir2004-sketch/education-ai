from database import get_db_connection


CONVERSATION_RETENTION_HOURS = 3


def create_tables():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations
        (
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '3 hours'),
            last_topic TEXT,
            follow_up_asked BOOLEAN DEFAULT FALSE,
            topic_understood BOOLEAN DEFAULT FALSE
        )
        """
    )
    cursor.execute(
        """
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP
        DEFAULT (CURRENT_TIMESTAMP + INTERVAL '3 hours')
        """
    )

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS last_topic TEXT
    """)

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS follow_up_asked BOOLEAN DEFAULT FALSE
    """)

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS topic_understood BOOLEAN DEFAULT FALSE
    """)

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS document_id TEXT
    """)

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS subject TEXT
    """)

    cursor.execute("""
        ALTER TABLE conversations
        ADD COLUMN IF NOT EXISTS topic TEXT
    """)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages
        (
            id SERIAL PRIMARY KEY,
            conversation_id INTEGER NOT NULL,
            role VARCHAR(20) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '3 hours')
        )
        """
    )
    cursor.execute(
        """
        ALTER TABLE messages
        ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP
        DEFAULT (CURRENT_TIMESTAMP + INTERVAL '3 hours')
        """
    )

    connection.commit()

    cursor.close()

    connection.close()


def cleanup_old_conversations():

    connection = get_db_connection()

    cursor = connection.cursor()

    try:
        cursor.execute(
            f"""
            DELETE FROM messages
            WHERE expires_at < CURRENT_TIMESTAMP
            """
        )

        cursor.execute(
            f"""
            DELETE FROM conversations
            WHERE expires_at < CURRENT_TIMESTAMP
            """
        )

        connection.commit()
    finally:
        cursor.close()
        connection.close()


def cleanup_expired_conversations_and_messages():
    """Backward-compatible alias for cleanup_old_conversations."""
    cleanup_old_conversations()


def create_conversation(
    user_id,
    document_id=None,
    subject=None,
    topic=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO conversations
        (
            user_id,
            document_id,
            subject,
            topic
        )
        VALUES
        (%s,%s,%s,%s)
        RETURNING id
        """,
        (user_id, document_id, subject, topic)
    )

    conversation_id = cursor.fetchone()[0]
    connection.commit()
    cursor.close()
    connection.close()
    return conversation_id


def get_active_conversation(
    user_id,
    document_id=None,
    subject=None,
    topic=None
):
    cleanup_old_conversations()

    connection = get_db_connection()
    cursor = connection.cursor()

    if document_id:
        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE user_id=%s
              AND document_id=%s
              AND expires_at > CURRENT_TIMESTAMP
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, document_id)
        )
    else:
        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE user_id=%s
              AND subject=%s
              AND topic=%s
              AND expires_at > CURRENT_TIMESTAMP
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            (user_id, subject, topic)
        )

    record = cursor.fetchone()
    cursor.close()
    connection.close()

    if record:
        return record[0]

    return create_conversation(
        user_id,
        document_id=document_id,
        subject=subject,
        topic=topic
    )


def save_message(
    conversation_id,
    role,
    message
):

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages
        (
            conversation_id,
            role,
            message,
            expires_at
        )
        VALUES
        (%s,%s,%s,CURRENT_TIMESTAMP + INTERVAL '3 hours')
        """,
        (
            conversation_id,
            role,
            message
        )
    )

    cursor.execute(
        """
        UPDATE conversations
        SET updated_at=CURRENT_TIMESTAMP,
            expires_at = CURRENT_TIMESTAMP + INTERVAL '3 hours'
        WHERE id=%s
        """,
        (
            conversation_id,
        )
    )

    connection.commit()

    cursor.close()

    connection.close()


def get_recent_messages(
    conversation_id,
    limit=10
):
    limit = max(1, int(limit))

    cleanup_old_conversations()

    connection = get_db_connection()

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT
            role,
            message
        FROM messages
        WHERE conversation_id=%s
        AND expires_at > CURRENT_TIMESTAMP
        ORDER BY created_at ASC
        LIMIT %s
        """,
        (
            conversation_id,
            limit
        )
    )
    records = cursor.fetchall()
    cursor.close()
    connection.close()
    return records
    

# New helper functions for learning state
def update_learning_state(
    conversation_id,
    last_topic=None,
    follow_up_asked=None,
    topic_understood=None
):

    connection = get_db_connection()
    cursor = connection.cursor()

    updates = []
    values = []

    if last_topic is not None:
        updates.append("last_topic=%s")
        values.append(last_topic)

    if follow_up_asked is not None:
        updates.append("follow_up_asked=%s")
        values.append(follow_up_asked)

    if topic_understood is not None:
        updates.append("topic_understood=%s")
        values.append(topic_understood)

    if updates:
        updates.append("updated_at=CURRENT_TIMESTAMP, expires_at=CURRENT_TIMESTAMP + INTERVAL '3 hours'")
        values.append(conversation_id)
        try:
            cursor.execute(
                f"UPDATE conversations SET {', '.join(updates)} WHERE id=%s",
                tuple(values)
            )
            connection.commit()
        finally:
            cursor.close()
            connection.close()
    else:
        cursor.close()
        connection.close()


def get_learning_state(conversation_id):

    if conversation_id is None:
        return None

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT last_topic,
               follow_up_asked,
               topic_understood
        FROM conversations
        WHERE id=%s
        """,
        (conversation_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if not row:
        return None

    return {
        "last_topic": row[0],
        "follow_up_asked": row[1],
        "topic_understood": row[2]
    }


def mark_topic_understood(conversation_id):

    update_learning_state(
        conversation_id,
        topic_understood=True,
        follow_up_asked=True
    )


def reset_follow_up_for_new_topic(
    conversation_id,
    topic
):

    update_learning_state(
        conversation_id,
        last_topic=topic,
        follow_up_asked=False,
        topic_understood=False
    )

def delete_document_conversations(document_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT id
            FROM conversations
            WHERE document_id=%s
            """,
            (document_id,)
        )

        conversation_ids = [row[0] for row in cursor.fetchall()]

        if conversation_ids:
            cursor.execute(
                """
                DELETE FROM messages
                WHERE conversation_id = ANY(%s)
                """,
                (conversation_ids,)
            )

        cursor.execute(
            """
            DELETE FROM conversations
            WHERE document_id=%s
            RETURNING id
            """,
            (document_id,)
        )

        deleted = len(cursor.fetchall())
        connection.commit()
        return deleted
    finally:
        cursor.close()
        connection.close()

create_tables()