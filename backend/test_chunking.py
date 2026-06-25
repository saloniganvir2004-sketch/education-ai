from utils import chunk_text

sample_text = """
Artificial Intelligence is a branch of computer science.

Machine Learning is a subset of AI.

Deep Learning is a subset of Machine Learning.

Natural Language Processing allows computers to understand language.
""" * 20

chunks = chunk_text(sample_text)

print(f"Total Chunks: {len(chunks)}")

for i, chunk in enumerate(chunks, start=1):
    print(f"\nChunk {i}")
    print("-" * 30)
    print(chunk[:100])