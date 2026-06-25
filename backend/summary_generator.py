from openai import OpenAI

from retriever import retrieve_chunks
from config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

SUMMARY_CACHE = {}


def generate_summary(document_id=None, subject=None, topic=None, parent_id=None):

    cache_key = str(parent_id or subject or document_id or "default")

    if cache_key in SUMMARY_CACHE:

        return {
            "summary": SUMMARY_CACHE[
                cache_key
            ]
        }

    chunks = retrieve_chunks(
        "summarize uploaded content",
        limit=10,
        document_id=document_id,
        subject=subject,
    )

    if not chunks:

        return {
            "summary": "No content found."
        }

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks
    )

    prompt = f"""
Create an educational summary.

Rules:
- Use only supplied content.
- Do not invent information.
- Keep summary concise.
- Include:
  1. Main Topics
  2. Key Concepts
  3. Important Points

CONTENT:
{context}
"""

    try:

        response = client.responses.create(
            model=settings.LLM_MODEL,
            input=prompt
        )

        summary = (
            response.output_text
            .strip()
        )

    except Exception as e:

        print(
            "SUMMARY ERROR:",
            e
        )

        return {
            "summary": "Summary generation failed."
        }

    SUMMARY_CACHE[
        cache_key
    ] = summary

    return {
        "summary": summary
    }