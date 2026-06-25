from openai import OpenAI

from retriever import retrieve_chunks
from config import settings




client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

ARCHITECTURE_CACHE = {}


def generate_architecture(document_id=None, subject=None, topic=None, parent_id=None):

    cache_key = str(parent_id or subject or document_id or "default")

    if cache_key in ARCHITECTURE_CACHE:

        return {
            "architecture": ARCHITECTURE_CACHE[
                cache_key
            ]
        }

    chunks = retrieve_chunks(
        "generate knowledge architecture from uploaded content",
        limit=20,
        document_id=document_id,
        subject=subject,
    )

    if not chunks:

        return {
            "architecture": "No content found."
        }

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks[:10]
    )

    prompt = f"""
Create a complete knowledge architecture.

Rules:
- Use ONLY supplied content.
- Do NOT invent facts.
- Identify:
  • Subject
  • Topics
  • Concepts
  • Definitions
  • Formulas (if present)
  • Important Questions (if present)
- Keep hierarchy clear.

Format:

Subject
├── Topic
│   ├── Concept
│   ├── Definition
│   ├── Formula
│   └── Questions
└── Topic

CONTENT:
{context}
"""

    try:

        response = client.responses.create(
            model=settings.LLM_MODEL,
            input=prompt
        )

        architecture = (
            response.output_text
            .strip()
        )

    except Exception as e:

        print(
            "ARCHITECTURE ERROR:",
            e
        )

        return {
            "architecture": "Architecture generation failed."
        }

    ARCHITECTURE_CACHE[
        cache_key
    ] = architecture

    return {
        "architecture": architecture
    }