from openai import OpenAI
import time

from config import settings

print("LOADED NEW EMBEDDINGS.PY")

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)

MAX_EMBEDDING_LENGTH = 3000

EMBEDDING_TIMEOUT = 20.0
EMBEDDING_CACHE = {}


def clean_text(text):

    text = str(
        text
    ).strip()

    return " ".join(
        text.split()
    )


def generate_embedding(
    text: str
):
    start = time.perf_counter()

    text = clean_text(
        text
    )

    if not text:

        raise ValueError(
            "Cannot generate embedding for empty text."
        )

    if len(text) > MAX_EMBEDDING_LENGTH:

        text = text[
            :MAX_EMBEDDING_LENGTH
        ]

    if text in EMBEDDING_CACHE:

        print(
            "EMBEDDING CACHE HIT"
        )

        print(
            "EMBEDDING TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return EMBEDDING_CACHE[
            text
        ]

    try:
        response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
        timeout=EMBEDDING_TIMEOUT
        )
        
        embedding = response.data[0].embedding

        EMBEDDING_CACHE[
            text
        ] = embedding

    except Exception as e:
        
        print(
            "EMBEDDING ERROR:",
            e
        )

        return None

    print(
        "EMBEDDING TIME:",
        round(
            time.perf_counter() - start,
            3
        ),
        "seconds"
    )

    return embedding


def generate_embeddings(
    texts
):
    start = time.perf_counter()

    cleaned_texts = []

    for text in texts:

        text = clean_text(
            text
        )

        if not text:
            continue

        if len(text) > MAX_EMBEDDING_LENGTH:

            text = text[
                :MAX_EMBEDDING_LENGTH
            ]

        cleaned_texts.append(
            text
        )

    if not cleaned_texts:

        print(
            "BATCH EMBEDDING TIME:",
            round(
                time.perf_counter() - start,
                3
            ),
            "seconds"
        )

        return []

    embeddings = [
        None
        for _ in cleaned_texts
    ]

    uncached_texts = []
    uncached_indexes = []

    for index, text in enumerate(
        cleaned_texts
    ):

        if text in EMBEDDING_CACHE:

            print(
                "BATCH CACHE HIT"
            )

            embeddings[
                index
            ] = EMBEDDING_CACHE[
                text
            ]

        else:

            uncached_texts.append(
                text
            )

            uncached_indexes.append(
                index
            )

    print(
        "NEW EMBEDDINGS GENERATED:",
        len(
            uncached_texts
        )
    )

    BATCH_SIZE = 100

    for i in range(
        0,
        len(uncached_texts),
        BATCH_SIZE
    ):

        batch = uncached_texts[
            i:i + BATCH_SIZE
        ]

        try:
            response = client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=batch,
                timeout=EMBEDDING_TIMEOUT
            )

            for offset, item in enumerate(
                response.data
            ):

                text = batch[
                    offset
                ]

                embedding = item.embedding

                EMBEDDING_CACHE[
                    text
                ] = embedding

                embeddings[
                    uncached_indexes[
                        i + offset
                    ]
                ] = embedding

        except Exception as e:

            print(
                "BATCH EMBEDDING ERROR:",
                e
            )

            for offset in range(len(batch)):
                embeddings[
                    uncached_indexes[i + offset]
                ] = None

    print(
        "BATCH EMBEDDING TIME:",
        round(
            time.perf_counter() - start,
            3
        ),
        "seconds"
    )

    return embeddings
