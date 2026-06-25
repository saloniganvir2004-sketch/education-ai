from vector_store import qdrant_client


COLLECTION_NAME = "education_chunks"


if qdrant_client.collection_exists(
    COLLECTION_NAME
):

    qdrant_client.delete_collection(
        collection_name=COLLECTION_NAME
    )

    print(
        "Collection deleted"
    )

else:

    print(
        "Collection does not exist"
    )