from openai import OpenAI

from retriever import retrieve_chunks
from config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

MINDMAP_CACHE = {}


def generate_mindmap(document_id=None, subject=None, topic=None, parent_id=None):

    cache_key = str(parent_id or subject or document_id or "default")

    if cache_key in MINDMAP_CACHE:

        return {
            "mindmap": MINDMAP_CACHE[
                cache_key
            ]
        }

    chunks = retrieve_chunks(
        "generate mind map from uploaded content",
        limit=20,
        document_id=document_id,
        subject=subject,
    )

    if not chunks:

        return {
            "mindmap": "No content found."
        }

    context = "\n\n".join(
        chunk["text"]
        for chunk in chunks[:10]
    )

    prompt = f"""
Create a hierarchical educational mind map.

Rules:
- Use ONLY supplied content.
- Do NOT invent facts.
- Identify main topic.
- Identify subtopics.
- Identify key concepts.
- Keep hierarchy clean.

Format:

Main Topic
├── Topic
│   ├── Concept
│   └── Concept
└── Topic

CONTENT:
{context}
"""

    try:

        response = client.responses.create(
            model=settings.LLM_MODEL,
            input=prompt
        )

        mindmap = (
            response.output_text
            .strip()
        )

    except Exception as e:

        print(
            "MINDMAP ERROR:",
            e
        )

        return {
            "mindmap": "Mindmap generation failed."
        }

    MINDMAP_CACHE[
        cache_key
    ] = mindmap

    return {
        "mindmap": mindmap
    }