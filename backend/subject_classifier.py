from document_registry import get_documents
import re


def detect_subject(question: str):
    """Return the most likely uploaded subject for a question.
    Uses uploaded subjects/topics instead of hardcoded keywords.
    """
    question = (question or "").lower()

    documents = get_documents()
    if not documents:
        return None

    scores = {}

    for doc in documents:
        if isinstance(doc, dict):
            subject = (doc.get("subject") or "").strip()
            topic = (doc.get("topic") or "").strip()
        else:
            # Tuple format from document_registry.get_documents()
            # Expected order: document_id, parent_id, filename, subject, topic, ...
            subject = (str(doc[3]) if len(doc) > 3 and doc[3] is not None else "").strip()
            topic = (str(doc[4]) if len(doc) > 4 and doc[4] is not None else "").strip()

        if not subject:
            continue

        score = scores.get(subject, 0)

        for word in subject.lower().split():
            if word and word in question:
                score += 5

        for word in topic.lower().split():
            if len(word) > 2 and word in question:
                score += 2

        scores[subject] = score

        # Strong topic matching
        topic_lower = topic.lower()

        if topic_lower and topic_lower in question:
            scores[subject] = scores.get(subject, 0) + 50

        if (
            "trigonometry" in topic_lower
            and (
                "angle of elevation" in question
                or "angle of depression" in question
                or "tower" in question
                or "height" in question
                or "distance" in question
            )
        ):
            scores[subject] = scores.get(subject, 0) + 100

    if not scores:
        return None

    best_subject = max(scores.items(), key=lambda x: x[1])

    if best_subject[1] == 0:
        # Fallback detection for mathematical expressions/questions
        math_patterns = [
            r"\d+\s*[+\-*/=]\s*\d+",
            r"\bx\b",
            r"\by\b",
            r"\bsolve\b",
            r"\bequation\b",
            r"\bangle\b",
            r"\btriangle\b",
            r"\btrigonometry\b",
            r"\bsin\b",
            r"\bcos\b",
            r"\btan\b",
            r"\bheight\b",
            r"\bdistance\b"
        ]

        if any(re.search(pattern, question) for pattern in math_patterns):
            return "Mathematics"

        return None

    return best_subject[0]