from utils import chunk_text
from embeddings import generate_embedding


sample_text = """
Artificial Intelligence is a branch of computer science.

Machine Learning is a subset of AI.

Deep Learning is a subset of Machine Learning.
""" * 10

chunks = chunk_text(sample_text)

results = []

for chunk in chunks:

    results.append(
        {
            "text": chunk,
            "embedding": generate_embedding(chunk)
        }
    )

print(f"Chunks: {len(results)}")

print(
    f"Embedding Dimension: "
    f"{len(results[0]['embedding'])}"
)