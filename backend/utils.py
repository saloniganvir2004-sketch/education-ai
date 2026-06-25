import re

from config import settings


def chunk_text(
    text,
    chunk_size=None,
    overlap_sentences=1
):

    if not text:
        return []

    if chunk_size is None:

        chunk_size = settings.CHUNK_SIZE

    original_text = str(text)

    text = str(text)

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    text = text.replace(
        "..",
        ". "
    )

    sentences = re.split(
        r'(?<=[.!?।])\s+',
        text
    )

    sentences = [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]

    chunks = []

    current_chunk = []
    current_length = 0

    for sentence in sentences:

        sentence_length = len(
            sentence
        )

        if (
            current_length
            + sentence_length
            <= chunk_size
        ):

            current_chunk.append(
                sentence
            )

            current_length += (
                sentence_length
            )

        else:

            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({"text": chunk_text})

            overlap = (
                current_chunk[
                    -overlap_sentences:
                ]
                if current_chunk
                else []
            )

            current_chunk = (
                overlap + [sentence]
            )

            current_length = len(
                " ".join(
                    current_chunk
                )
            )

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({"text": chunk_text})

    final_chunks = []

    last_search_end = 0

    for chunk in chunks:

        chunk_text = chunk["text"].strip()

        if not chunk_text:
            continue

        start_char = original_text.find(chunk_text, last_search_end)
        if start_char == -1:
            start_char = last_search_end
        end_char = start_char + len(chunk_text)
        last_search_end = end_char

        if len(chunk_text) < 100:
            if final_chunks:
                final_chunks[-1]["text"] += " " + chunk_text
                final_chunks[-1]["end_char"] = end_char
            else:
                final_chunks.append({
                    "text": chunk_text,
                    "start_char": start_char,
                    "end_char": end_char,
                })
            continue

        final_chunks.append(
            {
                "text": chunk_text,
                "start_char": start_char,
                "end_char": end_char,
            }
        )

    print(
        f"Created {len(final_chunks)} chunks"
    )

    return [
        {
            "text": chunk["text"],
            "start_char": chunk["start_char"],
            "end_char": chunk["end_char"],
        }
        for chunk in final_chunks
    ]