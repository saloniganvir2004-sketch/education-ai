from openai import OpenAI

from config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


def rewrite_query(question):

    if not question:

        return ""

    question = str(
        question
    ).strip()

    try:

        response = client.responses.create(
            model="gpt-5-nano",
            input=f"""
Rewrite the educational question for retrieval.

Rules:
- Keep original meaning.
- Fix grammar.
- Expand abbreviations if obvious.
- Return only the rewritten query.
- No explanation.

Question:
{question}
"""
        )

        rewritten = (
            response.output_text
            .strip()
        )

        if rewritten:
            return rewritten

    except Exception as e:

        print(
            "QUERY REWRITE ERROR:",
            e
        )

    return question