import re


def split_questions(question):

    if not question:
        return []

    question = str(
        question
    ).strip()

    separators = [
        r"\?",
        r"\n",
        r"\band\b",
        r"\balso\b"
    ]

    pattern = "|".join(
        separators
    )

    questions = re.split(
        pattern,
        question,
        flags=re.IGNORECASE
    )

    questions = [
        q.strip()
        for q in questions
        if q.strip()
    ]

    return questions