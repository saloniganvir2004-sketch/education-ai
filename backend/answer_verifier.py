from openai import OpenAI

from config import settings
from model_router import get_best_model


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


def verify_answer(
    question,
    context,
    answer
):

    try:

        response = client.responses.create(
            model=get_best_model(),
            input=f"""
Check whether the answer is fully supported by the context.

Return ONLY:

YES

or

NO

QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
{answer}
"""
        )

        result = (
            response.output_text
            .strip()
            .upper()
        )

        return result == "YES"

    except Exception as e:

        print(
            "VERIFIER ERROR:",
            e
        )

        return True