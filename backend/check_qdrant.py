from vector_store import qdrant_client


points, _ = qdrant_client.scroll(
    collection_name="education_chunks",
    limit=50,
    with_payload=True
)

print(
    "TOTAL POINTS:",
    len(points)
)

for i, point in enumerate(
    points,
    start=1
):

    print(
        f"\n{'=' * 80}"
    )

    print(
        "POINT:",
        i
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
        "PARENT ID:",
        point.payload.get(
            "parent_id",
            ""
        )
    )

    print(
        "SOURCE:",
        point.payload.get(
            "source",
            ""
        )
    )

    print(
        "TEXT:"
    )

    print(
        point.payload.get(
            "text",
            ""
        )[:500]
    )