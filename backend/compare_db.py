from difflib import SequenceMatcher
import math
import re
import time


COMPARE_CACHE_TTL_SECONDS = 300
COMPARE_CACHE = {}
EMBEDDING_COMPARE_CACHE = {}

STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    if not normalized:
        return []
    return [
        token
        for token in normalized.split()
        if token not in STOP_WORDS
    ]


def cosine_similarity(vector_a, vector_b) -> float:
    if not vector_a or not vector_b:
        return 0.0

    length = min(
        len(vector_a),
        len(vector_b)
    )
    if length == 0:
        return 0.0

    dot_product = sum(
        float(vector_a[index]) * float(vector_b[index])
        for index in range(length)
    )
    magnitude_a = math.sqrt(
        sum(
            float(value) ** 2
            for value in vector_a[:length]
        )
    )
    magnitude_b = math.sqrt(
        sum(
            float(value) ** 2
            for value in vector_b[:length]
        )
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return max(
        0.0,
        min(
            1.0,
            dot_product / (magnitude_a * magnitude_b)
        )
    )


def keyword_score(reference_answer: str, user_answer: str) -> float:
    reference_tokens = set(
        _tokenize(reference_answer)
    )
    user_tokens = set(
        _tokenize(user_answer)
    )

    if not reference_tokens and not user_tokens:
        return 1.0
    if not reference_tokens or not user_tokens:
        return 0.0

    overlap = reference_tokens.intersection(
        user_tokens
    )
    return len(overlap) / len(reference_tokens)


def extract_gaps(reference_answer: str, user_answer: str) -> list[str]:
    reference_tokens = []
    seen = set()

    for token in _tokenize(reference_answer):
        if token not in seen:
            reference_tokens.append(token)
            seen.add(token)

    user_tokens = set(
        _tokenize(user_answer)
    )

    return [
        token
        for token in reference_tokens
        if token not in user_tokens
    ][:8]


def _cache_key(reference_answer: str, user_answer: str) -> tuple[str, str]:
    return (
        normalize_text(reference_answer),
        normalize_text(user_answer)
    )


def _get_cached_comparison(cache_key):
    cached = COMPARE_CACHE.get(
        cache_key
    )
    if not cached:
        return None

    cached_at, value = cached
    if time.time() - cached_at > COMPARE_CACHE_TTL_SECONDS:
        del COMPARE_CACHE[
            cache_key
        ]
        return None

    return value


def _set_cached_comparison(cache_key, value):
    COMPARE_CACHE[
        cache_key
    ] = (
        time.time(),
        value
    )


def _generate_embedding(text: str):
    normalized = normalize_text(text)
    if not normalized:
        return None

    if normalized in EMBEDDING_COMPARE_CACHE:
        return EMBEDDING_COMPARE_CACHE[
            normalized
        ]

    try:
        from embeddings import generate_embedding

        embedding = generate_embedding(
            normalized
        )
    except Exception as error:
        print(
            "COMPARE EMBEDDING ERROR:",
            error
        )
        embedding = None

    if embedding:
        EMBEDDING_COMPARE_CACHE[
            normalized
        ] = embedding

    return embedding


def embedding_similarity(reference_answer: str, user_answer: str) -> float:
    reference_embedding = _generate_embedding(
        reference_answer
    )
    user_embedding = _generate_embedding(
        user_answer
    )

    if not reference_embedding or not user_embedding:
        return 0.0

    return cosine_similarity(
        reference_embedding,
        user_embedding
    )


def _sequence_similarity(reference_answer: str, user_answer: str) -> float:
    return SequenceMatcher(
        None,
        normalize_text(reference_answer),
        normalize_text(user_answer)
    ).ratio()


def _length_score(reference_answer: str, user_answer: str) -> float:
    reference_length = len(
        _tokenize(reference_answer)
    )
    user_length = len(
        _tokenize(user_answer)
    )

    if reference_length == 0 and user_length == 0:
        return 1.0
    if reference_length == 0 or user_length == 0:
        return 0.0

    ratio = min(
        reference_length,
        user_length
    ) / max(
        reference_length,
        user_length
    )
    return max(
        0.0,
        min(
            1.0,
            ratio
        )
    )


def confidence_score(
    answer_similarity: float,
    keyword_similarity: float,
    semantic_similarity: float,
    length_similarity: float
) -> float:
    if semantic_similarity > 0:
        return (
            semantic_similarity * 0.45
            + answer_similarity * 0.25
            + keyword_similarity * 0.20
            + length_similarity * 0.10
        )

    return (
        answer_similarity * 0.50
        + keyword_similarity * 0.35
        + length_similarity * 0.15
    )


def _generate_feedback(
    score: float,
    gaps: list[str]
) -> tuple[str, list[str]]:
    if score >= 0.85:
        return (
            "Strong answer. It closely matches the expected response.",
            []
        )

    suggestions = []
    if gaps:
        suggestions.append(
            "Include key ideas: "
            + ", ".join(gaps)
            + "."
        )

    if score >= 0.70:
        feedback = "Mostly correct, but it can be more complete."
    elif score >= 0.45:
        feedback = "Partially correct. Add the missing key points and improve detail."
    else:
        feedback = "The answer does not sufficiently match the expected response."

    return (
        feedback,
        suggestions
    )


def compare_answer(reference_answer: str, user_answer: str) -> dict:
    reference_answer = (reference_answer or "").strip()
    user_answer = (user_answer or "").strip()

    cache_key = _cache_key(
        reference_answer,
        user_answer
    )
    cached = _get_cached_comparison(
        cache_key
    )
    if cached:
        return cached

    answer_similarity = _sequence_similarity(
        reference_answer,
        user_answer
    )
    keyword_similarity = keyword_score(
        reference_answer,
        user_answer
    )
    semantic_similarity = embedding_similarity(
        reference_answer,
        user_answer
    )
    length_similarity = _length_score(
        reference_answer,
        user_answer
    )
    score = confidence_score(
        answer_similarity,
        keyword_similarity,
        semantic_similarity,
        length_similarity
    )
    gaps = extract_gaps(
        reference_answer,
        user_answer
    )
    feedback, suggestions = _generate_feedback(
        score,
        gaps
    )

    result = {
        "result": "YES" if score >= 0.70 else "NO",
        "similarity_score": round(score * 100, 2),
        "question_similarity": 100.0,
        "answer_similarity": round(answer_similarity * 100, 2),
        "keyword_similarity": round(keyword_similarity * 100, 2),
        "length_score": round(length_similarity * 100, 2),
        "confidence_score": round(score * 100, 2),
        "matched_question": None,
        "correct_answer": reference_answer,
        "suggestions": suggestions,
        "feedback": feedback,
    }

    _set_cached_comparison(
        cache_key,
        result
    )

    return result
