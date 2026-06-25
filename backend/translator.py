import re

from openai import OpenAI

from config import settings

from cache import (
    get_cached_answer,
    set_cached_answer
)


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


NUMBER_MAP = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "first": "1",
    "second": "2",
    "third": "3",
    "fourth": "4",
    "fifth": "5",
    "sixth": "6",
    "seventh": "7",
    "eighth": "8",
    "ninth": "9",
    "tenth": "10"
}


COMMON_HINGLISH_WORDS = {
    "kya",
    "kaun",
    "kaise",
    "kyun",
    "kab",
    "kahan",
    "kis",
    "kiska",
    "kiski",
    "kiske",
    "hai",
    "hain",
    "tha",
    "thi",
    "hoga",
    "hogi",
    "honge",
    "mera",
    "meri",
    "mere",
    "aap",
    "tum",
    "hum",
    "ham",
    "unka",
    "unki",
    "unke",
    "iska",
    "iski",
    "iske",
    "uska",
    "uski",
    "uske",
    "liye",
    "aur",
    "mein",
    "main",
    "samjhao",
    "samjhaiye",
    "bataye",
    "bataya",
    "batao",
    "janm",
    "adhyay",
    "kavita",
    "pad",
    "arth",
    "bhav",
    "ka",
    "ki",
    "ke",
    "par",
    "se",
    "ko"
}


def normalize_numbers(
    text
):

    text = str(text)

    words = text.split()

    normalized_words = []

    for word in words:

        clean_word = re.sub(
            r"[^\w]",
            "",
            word.lower()
        )

        if clean_word in NUMBER_MAP:

            normalized_words.append(
                NUMBER_MAP[clean_word]
            )

        else:

            normalized_words.append(
                word
            )

    return " ".join(
        normalized_words
    )


def detect_language(
    text
):

    text = str(
        text
    ).strip()

    if not text:

        return "english"

    hindi_chars = sum(
        1
        for char in text
        if "\u0900" <= char <= "\u097F"
    )

    latin_chars = sum(
        1
        for char in text
        if char.isascii()
        and char.isalpha()
    )

    if hindi_chars > 0 and latin_chars > 0:

        total = (
            hindi_chars +
            latin_chars
        )

        if hindi_chars / total > 0.60:

            return "hindi"

        return "hinglish"

    if hindi_chars > 0:

        return "hindi"

    cleaned_words = [
        re.sub(
            r"[^\w]",
            "",
            word.lower()
        )
        for word in text.split()
    ]

    cleaned_words = [
        word
        for word in cleaned_words
        if word
    ]

    english_command_patterns = [
        r"^state\s",
        r"^list\s",
        r"^name\s",
        r"^mention\s",
        r"^write\s",
        r"^discuss\s",
        r"^compare\s",
        r"^differentiate\s"
    ]

    lower_text = text.lower()

    english_question_patterns = [
        r"^who\s",
        r"^what\s",
        r"^when\s",
        r"^where\s",
        r"^why\s",
        r"^which\s",
        r"^how\s",
        r"^is\s",
        r"^are\s",
        r"^was\s",
        r"^were\s",
        r"^can\s",
        r"^could\s",
        r"^do\s",
        r"^does\s",
        r"^did\s",
        r"^explain\s",
        r"^describe\s",
        r"^define\s",
        r"^tell me",
        r"^give me"
    ]

    for pattern in english_question_patterns:

        if re.match(
            pattern,
            lower_text
        ):

            return "english"

    for pattern in english_command_patterns:

        if re.match(
            pattern,
            lower_text
        ):

            return "english"

    hinglish_matches = sum(
        1
        for word in cleaned_words
        if word in COMMON_HINGLISH_WORDS
    )

    total_words = len(
        cleaned_words
    )

    if (
        total_words >= 3
        and hinglish_matches >= 2
    ):

        return "hinglish"

    if (
        total_words > 0
        and hinglish_matches / total_words >= 0.30
    ):

        return "hinglish"

    return "english"


def normalize_question(
    question
):

    question = str(
        question
    )

    question = normalize_numbers(
        question
    )

    question = question.strip()

    question = re.sub(
        r"[^\w\s\u0900-\u097F]",
        " ",
        question,
        flags=re.UNICODE
    )

    question = re.sub(
        r"\s+",
        " ",
        question
    )

    return (
        question
        .strip()
        .lower()
    )


def translate_to_english(
    text
):

    text = str(
        text
    ).strip()

    if not text:

        return text

    language = detect_language(
        text
    )

    if language == "english":

        return normalize_numbers(
            text
        )

    cache_key = (
        "translation::"
        + normalize_question(
            text
        )
    )

    cached_translation = (
        get_cached_answer(
            cache_key
        )
    )

    if cached_translation:

        print(
            "TRANSLATION CACHE HIT"
        )

        return cached_translation

    try:

        response = client.responses.create(
            model=settings.LLM_MODEL,
            input=f"""
Convert the user's query into an English retrieval query.

Rules:
- Return English only.
- Preserve the user's intent exactly.
- Preserve names, technical terms, formulas, chapter titles, product names, and entities exactly as written.
- If the query depends on previous conversation, preserve that dependency instead of inventing missing context.
- Never guess or hallucinate missing information.
- Never replace pronouns with assumed names.
- Never insert chapter names, document names, numbers, or entities that are not explicitly present.
- Do not answer the question.
- Do not explain the question.
- Return only the translated retrieval query.

Question:
{text}
"""
        )

        translated = str(
            getattr(
                response,
                "output_text",
                ""
            ) or ""
        ).strip()

        translated = (
            normalize_numbers(
                translated
            )
        )
        if not translated:
            return normalize_numbers(text)

        print(
            "INPUT QUESTION:",
            text
        )

        print(
            "DETECTED LANGUAGE:",
            language
        )

        print(
            "TRANSLATED QUESTION:",
            translated
        )

        if translated:

            set_cached_answer(
                cache_key,
                translated
            )

            return translated

    except Exception as e:

        print(
            "TRANSLATION ERROR:",
            e
        )

    return normalize_numbers(
        text
    )


def is_same_language_family(
    question_language,
    file_language
):

    question_language = str(
        question_language
    ).lower()

    file_language = str(
        file_language
    ).lower()

    hindi_family = {
        "hi",
        "hindi",
        "hinglish"
    }
    english_family = {
        "en",
        "english"
    }
    if (
        question_language
        in hindi_family
        and file_language
        in hindi_family
    ):
        return True

    if (
        question_language
        in english_family
        and file_language
        in english_family
    ):
        return True
    return (
        question_language
        == file_language
    )