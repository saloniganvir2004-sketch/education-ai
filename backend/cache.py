import hashlib
import redis
import time

from config import settings

from upload_history_db import (
    get_latest_document
)


CACHE_EXPIRY_SECONDS = 86400
LOCAL_CACHE = {}


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)


def build_cache_key(
    question,
    user_id=None,
    document_id=None
):

    latest_document = get_latest_document()
    if document_id:
        parent_id = document_id
    elif latest_document:
        parent_id = latest_document["parent_id"]
    else:
        parent_id = "global"

    if not user_id:

        user_id = "anonymous"

    raw_key = (
        f"{user_id}::"
        f"{parent_id}::"
        f"{str(question).strip().lower()}"
    )

    return hashlib.md5(
        raw_key.encode(
            "utf-8"
        )
    ).hexdigest()


def get_cached_answer(
    question,
    user_id=None,
    document_id=None
):
    start = time.perf_counter()

    cache_key = build_cache_key(
        question,
        user_id,
        document_id=document_id
    )

    if cache_key in LOCAL_CACHE:

        print(
            "LOCAL CACHE HIT"
        )

        print(
            "CACHE LOOKUP:",
            round(
                time.perf_counter() - start,
                4
            ),
            "seconds"
        )

        return LOCAL_CACHE[
            cache_key
        ]

    try:
        answer = redis_client.get(
            cache_key
        )

    except Exception as e:
        print(
            "REDIS CACHE ERROR:",
            e
        )
        
        answer = None

    if answer:

        print(
            "CACHE HIT"
        )

        print(
            "REDIS CACHE HIT"
        )

        LOCAL_CACHE[
            cache_key
        ] = answer

    print(
        "CACHE LOOKUP:",
        round(
            time.perf_counter() - start,
            4
        ),
        "seconds"
    )

    return answer


def set_cached_answer(
    question,
    answer,
    user_id=None,
    document_id=None
):

    cache_key = build_cache_key(
        question,
        user_id,
        document_id=document_id
    )

    LOCAL_CACHE[
        cache_key
    ] = answer

    try:
        redis_client.set(
            cache_key,
            answer,
            ex=CACHE_EXPIRY_SECONDS
        )

    except Exception as e:
        print(
            "REDIS CACHE ERROR:",
            e
        )


def delete_cached_answer(
    question,
    user_id=None,
    document_id=None
):

    cache_key = build_cache_key(
        question,
        user_id,
        document_id=document_id
    )

    if cache_key in LOCAL_CACHE:
        del LOCAL_CACHE[
            cache_key
        ]

    try:
        redis_client.delete(
            cache_key
        )

    except Exception as e:
        print(
            "REDIS CACHE ERROR:",
            e
        )


def clear_cache():

    LOCAL_CACHE.clear()

    try:
        redis_client.flushdb()

    except Exception as e:
        print(
            "REDIS CACHE ERROR:",
            e
        )
