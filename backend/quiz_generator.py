from openai import OpenAI

from retriever import retrieve_chunks
from config import settings

from upload_history_db import (
    get_latest_document
)


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

QUIZ_CACHE = {}


def generate_quiz():

    latest_document = get_latest_document()

    if not latest_document:
        return {
            "quiz": "No content found."
        }

    parent_id = latest_document["parent_id"]

    if not parent_id:
        return {
            "quiz": "No content found."
        }

    cache_key = str(
        parent_id
    )

    if cache_key in QUIZ_CACHE:

        return {
            "quiz": QUIZ_CACHE[
                cache_key
            ]
        }

    chunks = retrieve_chunks(
        "generate questions from uploaded content",
        document_id=latest_document["document_id"],
        limit=20,
    )

    if chunks:
        print("QUIZ CHUNKS:", len(chunks))

    if not chunks:

        return {
            "quiz": "No content found."
        }

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks[:10]
    )

    prompt = f"""
Generate educational MCQs from the supplied content.

Rules:
- Use only supplied content.
- Do not invent facts.
- Create exactly 10 MCQs.
- Each question must have 4 options.
- Only one correct answer.
- Cover different topics.
- Return only MCQs.

CONTENT:
{context}
"""

    try:

        response = client.responses.create(
            model=settings.LLM_MODEL,
            input=prompt
        )

        quiz = (
            response.output_text
            .strip()
        )

    except Exception as e:

        print(
            "QUIZ ERROR:",
            e
        )

        return {
            "quiz": "Quiz generation failed."
        }

    QUIZ_CACHE[
        cache_key
    ] = quiz

    return {
        "quiz": quiz
    }