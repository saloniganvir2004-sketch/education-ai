from embeddings import generate_embedding
from vector_store import qdrant_client


query = "What is Artificial Intelligence?"

query_embedding = generate_embedding(
    query
)

results = qdrant_client.query_points(
    collection_name="education_chunks",
    query=query_embedding,
    limit=10
)

print(
    "RESULT COUNT:",
    len(results.points)
)

for index, point in enumerate(
    results.points,
    start=1
):

    print(
        f"\n{'=' * 80}"
    )

    print(
        "RANK:",
        index
    )

    print(
        "SCORE:",
        point.score
    )

    print(
        "FILE:",
        point.payload.get(
            "file_name",
            ""
        )
    )

    print(
        "CHUNK INDEX:",
        point.payload.get(
            "chunk_index",
            0
        )
    )

    print(
        point.payload.get(
            "text",
            ""
        )[:300]
    )