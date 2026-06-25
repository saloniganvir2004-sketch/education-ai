from vector_store import qdrant_client

collections = qdrant_client.get_collections()

for c in collections.collections:
    print(c.name)