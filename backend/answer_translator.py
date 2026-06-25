from openai import OpenAI

from config import settings

from cache import (
    get_cached_answer,
    set_cached_answer
)


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


NOT_FOUND_MESSAGES = [
    "Information not found in the provided content.",
    "प्रदान की गई सामग्री में जानकारी नहीं मिली।",
    "प्रदान की गई सामग्री में सूचना नहीं मिली।",
    "प्रदान की गई सामग्री में सूचना नहीं मिली.",
    "उत्तर: प्रदान की गई सामग्री में जानकारी नहीं मिली।",
    "उत्तर: प्रदान की गई सामग्री में सूचना नहीं मिली।"
]


def translate_answer(
    answer,
    language
):

    if not answer:
        return ""

    answer = str(
        answer
    ).strip()
    language = (
        str(language or "english")
        .strip()
        .lower()
    )

    cache_key = (
        "answer_translation::"
        + language
        + "::"
        + answer
    )

    cached_translation = None

    if language == "english":
        cached_translation = get_cached_answer(cache_key)
    elif language not in ("hindi", "hinglish"):
        cached_translation = get_cached_answer(cache_key)

    if cached_translation:

        print(
            "ANSWER TRANSLATION CACHE HIT"
        )

        return cached_translation

    if answer in NOT_FOUND_MESSAGES:

        if language == "hindi":
            message = "प्रदान की गई सामग्री में जानकारी नहीं मिली।"
            set_cached_answer(cache_key, message)
            return message

        if language == "hinglish":
            message = "Di gayi content mein jaankari nahi mili."
            set_cached_answer(cache_key, message)
            return message

        message = "Information not found in the provided content."
        set_cached_answer(cache_key, message)
        return message

    if language == "english":
        set_cached_answer(cache_key, answer)
        return answer

    if language == "hinglish":
        try:
            response = client.responses.create(
                model=settings.LLM_MODEL,
                input=f"""
Translate the following English answer into natural Hinglish (Hindi written in English letters).

Rules:
- Return only Hinglish.
- Preserve facts exactly.
- Preserve names exactly.
- Do not add or remove information.

Answer:
{answer}
"""
            )

            translated = str(
                getattr(response, "output_text", "") or ""
            ).strip()
            print("Detected language:", language)
            print("Original answer:", answer)
            print("Translated answer:", translated)

            if translated:
                set_cached_answer(
                    cache_key,
                    translated
                )
                return translated

            return answer
        except Exception as e:
            print(
                "TRANSLATION ERROR:",
                e
            )
            return answer

    try:

        if language == "hindi":

            response = client.responses.create(
                model=settings.LLM_MODEL,
                input=f"""
Translate the following English answer into natural Hindi.

Return ONLY Hindi text written in Devanagari script.
Do not return English.
Do not return Hinglish.
Do not mix English and Hindi.
Preserve names and facts exactly.

English Answer:
{answer}
"""
            )

        else:

            return answer

        translated = str(
            getattr(
                response,
                "output_text",
                ""
            ) or ""
        ).strip()
        
        translated = (
            translated
            .replace("Answer:", "")
            .replace("उत्तर:", "")
            .strip()
        )

        print("Detected language:", language)
        print("Original answer:", answer)
        print("Translated answer:", translated)

        if language == "hindi":
            has_devanagari = any('\u0900' <= ch <= '\u097F' for ch in translated)
            if not has_devanagari:
                raise ValueError("Translation did not contain Devanagari text.")

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

    print("Translation failed. Returning original answer.")
    return answer