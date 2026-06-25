from retriever import retrieve_chunks


results = retrieve_chunks(
    "What is Artificial Intelligence?"
)

print(
    "Retrieved Chunks:",
    len(results)
)

for index, item in enumerate(
    results,
    start=1
):

    print(
        f"\n{'=' * 80}"
    )

    print(
        "Rank:",
        index
    )

    print(
        "Score:",
        item.get(
            "score",
            0
        )
    )

    print(
        "Combined Score:",
        item.get(
            "combined_score",
            0
        )
    )

    print(
        "File:",
        item.get(
            "file_name",
            ""
        )
    )

    print(
        "Chunk Index:",
        item.get(
            "chunk_index",
            0
        )
    )

    print(
        "Parent ID:",
        item.get(
            "parent_id",
            ""
        )
    )

    print(
        "Text Preview:"
    )

    print(
        item.get(
            "text",
            ""
        )[:300]
    )