from embeddings import generate_embedding

embedding = generate_embedding(
    "What is Artificial Intelligence?"
)

print("Embedding Generated")
print(len(embedding))