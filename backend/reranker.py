import re


TOP_RERANKED_CHUNKS = 15


def normalize_words(text):

    return {
        re.sub(r'[^a-z0-9]', '', word.lower())
        for word in str(text).split()
        if word.strip()
    }



def rerank_chunks(
    question,
    chunks
):

    if not chunks:
        return []

    scored_chunks = []

    question_words = normalize_words(
        question
    )

    for chunk in chunks:

        text = chunk.get(
            "text",
            ""
        )

        text_words = normalize_words(
            text
        )

        overlap = len(
            question_words.intersection(
                text_words
            )
        )

        vector_score = float(
            chunk.get(
                "score",
                0
            )
        )

        combined_score = float(
            chunk.get(
                "combined_score",
                0
            )
        )

        rerank_score = (
            vector_score * 100
        ) + (
            overlap * 20
        ) + (
            combined_score * 0.1
        )

        chunk["rerank_score"] = round(
            rerank_score,
            4
        )

        scored_chunks.append(
            chunk
        )

    scored_chunks.sort(
        key=lambda x: (
            x.get(
                "rerank_score",
                0
            ),
            x.get(
                "combined_score",
                0
            ),
            x.get(
                "score",
                0
            )
        ),
        reverse=True
    )

    print(
        "RERANKED SCORES:",
        [
            item.get(
                "rerank_score",
                0
            )
            for item in scored_chunks[:10]
        ]
    )

    return scored_chunks[
        :TOP_RERANKED_CHUNKS
    ]