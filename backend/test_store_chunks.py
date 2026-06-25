from utils import chunk_text
from embeddings import generate_embedding
from vector_store import store_chunks


sample_text = """
Artificial Intelligence is a branch of computer science.

Machine Learning is a subset of AI.

Deep Learning is a subset of Machine Learning.
""" * 10

chunks = chunk_text(sample_text)

embeddings = []

for chunk in chunks:

    embeddings.append(
        {
            "text": chunk,
            "embedding": generate_embedding(chunk),
            "source": "test",
            "file_name": "test.txt",
            "chunk_id": "test_chunk",
            "parent_id": "test_parent",
            "chunk_index": 1,
            "total_chunks": len(chunks)
        }
    )

store_chunks(
    "education_chunks",
    embeddings
)

print(
    "Chunks Stored Successfully"
)