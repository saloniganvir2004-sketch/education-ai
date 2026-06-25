from datetime import datetime
from typing import List, Dict, Any

DEBUG_RAG = True


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")


def _line():
    print("=" * 80)


def _section(title: str):
    if not DEBUG_RAG:
        return
    print()
    _line()
    print(f"[{_timestamp()}] {title}")
    _line()


def log_ingestion_start(
    filename: str,
    subject: str,
    topic: str,
    document_id: str = "",
):
    if not DEBUG_RAG:
        return

    _section("INGESTION START")

    print(f"File        : {filename}")
    print(f"Subject     : {subject}")
    print(f"Topic       : {topic}")
    print(f"Document ID : {document_id}")


def log_text_extraction(
    characters: int,
    pages=None,
    language=None,
):
    if not DEBUG_RAG:
        return

    _section("TEXT EXTRACTION")

    print(f"Characters : {characters}")

    if pages is not None:
        print(f"Pages      : {pages}")

    if language:
        print(f"Language   : {language}")


def log_chunking(chunks: List[str]):
    if not DEBUG_RAG:
        return

    _section("CHUNKING")

    print(f"Total Chunks : {len(chunks)}")

    for index, chunk in enumerate(chunks, start=1):
        preview = chunk.replace("\n", " ")
        preview = preview[:120]

        print(f"\nChunk {index}")
        print(f"Length  : {len(chunk)}")
        print(f"Preview : {preview}")


# 1. Add log_chunk_metadata below log_chunking
def log_chunk_metadata(chunks):
    if not DEBUG_RAG:
        return
    _section("CHUNK METADATA")
    for chunk in chunks:
        print(
            f"Chunk={chunk.get('chunk_index')} | "
            f"Subject={chunk.get('subject')} | "
            f"Topic={chunk.get('topic')} | "
            f"Page={chunk.get('page')} | "
            f"Document={chunk.get('document_id')}"
        )


def log_embedding_progress(current: int, total: int):
    if not DEBUG_RAG:
        return

    print(f"Embedding {current}/{total}")


def log_storage(
    chunk_count: int,
    subject: str,
    topic: str,
):
    if not DEBUG_RAG:
        return

    _section("VECTOR STORAGE")

    print(f"Chunks Stored : {chunk_count}")
    print(f"Subject       : {subject}")
    print(f"Topic         : {topic}")


def log_retrieval_start(
    question: str,
    subject: str,
    topic: str,
):
    if not DEBUG_RAG:
        return

    _section("RETRIEVAL")

    print(f"Question      : {question}")
    print(f"Subject       : {subject}")
    print(f"Primary Topic : {topic}")


def log_cross_topic_search(
    retrieved_chunks: List[Dict[str, Any]]
):
    if not DEBUG_RAG:
        return

    _section("CROSS TOPIC SEARCH")

    grouped = {}

    for chunk in retrieved_chunks:
        topic = chunk.get("topic", "Unknown")
        grouped.setdefault(topic, []).append(chunk)

    for topic, chunks in grouped.items():
        print(f"\nTopic : {topic}")
        print(f"Chunks: {len(chunks)}")


# 2. Add log_topic_summary below log_cross_topic_search
def log_topic_summary(retrieved_chunks):
    if not DEBUG_RAG:
        return
    _section("TOPIC SUMMARY")
    summary = {}
    for chunk in retrieved_chunks:
        topic = chunk.get("topic", "Unknown")
        summary[topic] = summary.get(topic, 0) + 1
    for topic, count in summary.items():
        print(f"{topic}: {count} chunks")


# 3. Add log_search_path below log_topic_summary
def log_search_path(primary_topic, searched_topics):
    if not DEBUG_RAG:
        return
    _section("SEARCH PATH")
    print(f"Primary: {primary_topic}")
    for topic in searched_topics:
        if topic != primary_topic:
            print(f"Cross : {topic}")


def log_ranking(
    retrieved_chunks: List[Dict[str, Any]]
):
    if not DEBUG_RAG:
        return

    _section("RANKING")

    ordered = sorted(
        retrieved_chunks,
        key=lambda x: x.get("score", 0),
        reverse=True,
    )

    for i, chunk in enumerate(ordered, start=1):
        subject = chunk.get("subject", "")
        topic = chunk.get("topic", "")
        document_id = chunk.get("document_id", "")
        score = chunk.get("score", 0)
        page_start = chunk.get("page_start")
        page_end = chunk.get("page_end")
        page = chunk.get("page")
        # Fallback logic for page range
        if page_start is not None and page_end is not None:
            pages_str = f"{page_start}-{page_end}"
        elif page is not None:
            pages_str = str(page)
        else:
            pages_str = ""
        print(f"{i:02d}.")
        print(f"Subject : {subject}")
        print(f"Topic   : {topic}")
        print(f"Document: {document_id}")
        print(f"Pages   : {pages_str}")
        print(f"Score   : {score}")


def log_answer_sources(
    retrieved_chunks: List[Dict[str, Any]]
):
    if not DEBUG_RAG:
        return

    _section("ANSWER SOURCES")

    seen = set()

    for chunk in retrieved_chunks:
        key = (
            chunk.get("subject"),
            chunk.get("topic"),
        )

        if key in seen:
            continue

        seen.add(key)

        print(
            f"{chunk.get('subject')} -> {chunk.get('topic')}"
        )


# 4. Add log_final_summary below log_answer_sources
def log_final_summary(retrieval_time, retrieved_chunks):
    if not DEBUG_RAG:
        return
    _section("FINAL SUMMARY")
    # Unique documents
    unique_documents = set()
    unique_topics = set()
    unique_pages = set()
    for chunk in retrieved_chunks:
        document_id = chunk.get("document_id")
        if document_id:
            unique_documents.add(document_id)
        topic = chunk.get("topic")
        if topic:
            unique_topics.add(topic)
        # Page range logic
        page_start = chunk.get("page_start")
        page_end = chunk.get("page_end")
        page = chunk.get("page")
        if page_start is not None and page_end is not None:
            for p in range(int(page_start), int(page_end) + 1):
                unique_pages.add(p)
        elif page is not None:
            unique_pages.add(int(page))
    print(f"Retrieval Time : {retrieval_time:.3f}s")
    print(f"Documents      : {len(unique_documents)}")
    print(f"Topics         : {len(unique_topics)}")
    print(f"Pages Used     : {len(unique_pages)}")
    print(f"Chunks         : {len(retrieved_chunks)}")
    print("Topic Sources:")
    for topic in sorted(unique_topics):
        print(f" - {topic}")
    print("Page Ranges:")
    for chunk in retrieved_chunks:
        topic = chunk.get("topic", "")
        page_start = chunk.get("page_start")
        page_end = chunk.get("page_end")
        page = chunk.get("page")
        if page_start is not None and page_end is not None:
            pages_str = f"{page_start}-{page_end}"
        elif page is not None:
            pages_str = str(page)
        else:
            pages_str = ""
        print(f" - {topic}: {pages_str}")


def log_ingestion_complete():
    if not DEBUG_RAG:
        return

    _section("INGESTION COMPLETED")


def log_answer_complete():
    if not DEBUG_RAG:
        return

    _section("ANSWER GENERATED")