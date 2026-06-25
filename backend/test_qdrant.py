from vector_store import (
    qdrant_client,
    EMBEDDING_DIMENSION
)

COLLECTION_NAME = "education_chunks"

if not qdrant_client.collection_exists(
    COLLECTION_NAME
):

    print(
        "Collection Missing"
    )

else:

    info = qdrant_client.get_collection(
        COLLECTION_NAME
    )

    print(
        "Collection Exists"
    )

    print(
        "Expected Dimension:",
        EMBEDDING_DIMENSION
    )

    print(
        "Collection Info:"
    )

    print(info)