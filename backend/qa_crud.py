from vector_store import get_connection


def get_all_qa_pairs():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, question, answer
        FROM qa_pairs
        ORDER BY id DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def get_qa_pair_by_id(qa_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, question, answer
        FROM qa_pairs
        WHERE id = %s
    """, (qa_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def update_qa_pair(qa_id, question, answer):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE qa_pairs
        SET
            question = %s,
            answer = %s
        WHERE id = %s
    """, (
        question,
        answer,
        qa_id
    ))

    conn.commit()

    updated = cur.rowcount > 0

    cur.close()
    conn.close()

    return updated

def delete_qa_pair(qa_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM qa_pairs
        WHERE id = %s
    """, (qa_id,))

    conn.commit()

    deleted = cur.rowcount > 0

    cur.close()
    conn.close()

    return deleted


def add_qa_pair(question, answer):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO qa_pairs (question, answer)
        VALUES (%s, %s)
        RETURNING id, question, answer
        """,
        (question, answer)
    )

    row = cur.fetchone()

    conn.commit()

    cur.close()
    conn.close()

    return row