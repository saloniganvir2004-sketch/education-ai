from openai import OpenAI
from routes.subject_routes import router as subject_router
from routes.qa_routes import router as qa_router
from routes.document_routes import router as document_router
from fastapi import FastAPI
app = FastAPI()
app.include_router(subject_router)
app.include_router(
    qa_router,
    prefix="/qa",
    tags=["QA Management"],
)
# Document routes (including /documents/{document_id}/overview)
app.include_router(
    document_router,
    prefix="/documents",
    tags=["Documents"],
)

# Diagnostic startup prints
print("Subject router registered")
print("QA router registered")
print("Document router registered")
import asyncio
import time
from debug_logger import log_final_summary
from intent_classifier import classify_intent, Intent
from cache import (
    get_cached_answer,
    set_cached_answer
)
from qa_db import (
    add_qa_pair,
    get_similar_qa_answer
)
from math_detector import is_math_question
from math_solver import solve_math_question
from upload_history_db import (
    get_latest_document
)
from vector_store import delete_document_chunks
from qa_db import delete_document_qa_pairs
from task_db import delete_document_tasks
from unanswered_db import delete_document_unanswered_questions
from upload_history_db import delete_document_upload_history
from retriever import retrieve_chunks
from answer_translator import (
    translate_answer
)
from translator import (
    normalize_question,
    detect_language,
    translate_to_english
)
from subject_classifier import detect_subject
from config import settings
from task_db import (
    create_task,
    update_task
)
from unanswered_db import (
    add_unanswered_question
)
from conversation_db import (
    get_active_conversation,
    save_message,
    get_recent_messages,
    get_learning_state,
    reset_follow_up_for_new_topic,
    mark_topic_understood,
    delete_document_conversations,
)
client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)
NOT_FOUND_MESSAGE = (
    "Information not found in the provided content."
)
BAD_PHRASES = [
    "information not found",
    "सूचना नहीं मिली",
    "जानकारी नहीं मिली",
    "provided content",
    "information mil",
    "content mein information",
    "content mein suchna"
]
def clean_answer(answer):

    if not answer:
        return ""
    answer = str(answer)
    answer = answer.replace(
        "\n",
        " "
    )
    while "  " in answer:

        answer = answer.replace(
            "  ",
            " "
        )
    return answer.strip()
def is_bad_answer(answer):
    if not answer:
        return True
    answer_lower = str(
        answer
    ).lower()
    return any(
        phrase.lower()
        in answer_lower
        for phrase in BAD_PHRASES
    )
def build_context(chunks):
    expanded_chunks = []
    seen = set()
    for chunk in chunks:
        text = chunk.get(
            "text",
            ""
        )
        source_label = chunk.get(
            "source_label",
            "Unknown > Unknown"
        )

        formatted_text = (
            f"[Source: {source_label}]\n\n{text}"
        )

        if text and text not in seen:
            expanded_chunks.append(
                formatted_text
            )
            seen.add(
                text
            )
    return "\n\n".join(
        expanded_chunks
    )
def build_conversation_history(
    user_id
):
    # Cleanup expired conversations and messages before fetching
    from conversation_db import cleanup_expired_conversations_and_messages
    cleanup_expired_conversations_and_messages()

    latest_document = get_latest_document()
    document_id = latest_document.get("document_id") if latest_document else None
    subject = latest_document.get("subject") if latest_document else None
    topic = latest_document.get("topic") if latest_document else None

    conversation_id = get_active_conversation(
        user_id,
        document_id=document_id,
        subject=subject,
        topic=topic,
    )
    messages = (
        get_recent_messages(
            conversation_id,
            limit=30
        )
    )
    history = []
    for role, message in messages:
        if role == "user":
            history.append(
                f"User: {message}"
            )
        else:
            history.append(
                f"Assistant: {message}"
            )
    return (
        conversation_id,
        "\n".join(history)
    )
async def run_rag_pipeline(
    question,
    user_id,
    task_id=None,
    language="english",
    learning_state=None
):
    retrieval_start_time = time.perf_counter()
    conversation_id, conversation_history = (
        build_conversation_history(
            user_id
        )
    )

    previous_user_question = ""

    if conversation_history.strip():
        for line in reversed(conversation_history.split("\n")):
            if line.startswith("User:"):
                previous_user_question = line.replace("User:", "", 1).strip()
                if previous_user_question.lower() != question.lower():
                    break
    if learning_state is None:
        learning_state = get_learning_state(conversation_id)

    translated_question = translate_to_english(
        question
    )
    from subject_classifier import detect_subject
    latest_document = get_latest_document()
    document_id = None
    subject = None
    topic = None

    if latest_document:
        document_id = latest_document.get("document_id")
        subject = latest_document.get("subject")
        topic = latest_document.get("topic")
    else:
        subject = detect_subject(translated_question)
    retrieval_question = translated_question

    intent = classify_intent(question)

    if (
        intent == Intent.FOLLOW_UP
        and previous_user_question
    ):
        retrieval_question = (
            f"{previous_user_question}\n\nFollow-up: {translated_question}"
        )

    if conversation_history.strip():
        try:
            rewrite_prompt = f"""
Conversation history:
{conversation_history}
Current question:
{translated_question}
Rewrite the current question into a standalone question using the conversation history only to resolve references such as he, she, it, this, that, then, next, after that, uske baad, phir, fir.
Return only the rewritten standalone question in English.
If the current question is already standalone, return it unchanged.
Resolve pronouns (he, she, it, they, this, that, him, her, them) only using the provided conversation history.
Never invent or guess missing entities.
"""
            rewrite_response = await asyncio.to_thread(
                client.responses.create,
                model=settings.LLM_MODEL,
                input=rewrite_prompt
            )
            retrieval_question = clean_answer(rewrite_response.output_text) or translated_question
            print("REWRITTEN QUESTION:", retrieval_question)
        except Exception:
            retrieval_question = translated_question

    normalized_question = normalize_question(
        retrieval_question
    )
    print("CONVERSATION HISTORY:")
    print(conversation_history)
    print(
        "ORIGINAL QUESTION:",
        question
    )
    print(
        "TRANSLATED QUESTION (EN):",
        translated_question
    )

    retrieved_chunks = retrieve_chunks(
        retrieval_question,
        limit=settings.TOP_K,
        document_id=document_id,
        subject=subject,
    )
    if retrieved_chunks is None:
        retrieved_chunks = []
    # Use the actual retrieved source as the active context.
    # This prevents the latest uploaded document/topic from overriding retrieval results.
    print("RETRIEVED CHUNKS COUNT:", len(retrieved_chunks))
    if retrieved_chunks:
        first_chunk = retrieved_chunks[0]

        document_id = (
            first_chunk.get("document_id")
            or first_chunk.get("parent_id")
            or document_id
        )

        subject = (
            first_chunk.get("subject")
            or subject
        )

        topic = (
            retrieved_chunks[0].get("topic")
            if retrieved_chunks and retrieved_chunks[0].get("topic")
            else topic
        )
        print("FIRST CHUNK SUBJECT:", first_chunk.get("subject"))
        print("FIRST CHUNK TOPIC:", first_chunk.get("topic"))
        print("FIRST CHUNK DOCUMENT:", first_chunk.get("document_id"))

    retrieved_sources = [
        {
            "subject": chunk.get("subject"),
            "topic": chunk.get("topic"),
            "filename": chunk.get("file_name") or chunk.get("filename"),
            "page": chunk.get("page"),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "score": chunk.get("score"),
            "source_label": chunk.get("source_label"),
        }
        for chunk in retrieved_chunks
    ]
    retrieval_trace = (
        retrieved_chunks[0].get("retrieval_trace", {})
        if retrieved_chunks else {}
    )

    confidence = 0.0
    if retrieved_chunks:
        first_score = retrieved_chunks[0].get("score")
        if first_score is not None:
            try:
                confidence = float(first_score)
            except (TypeError, ValueError):
                confidence = 0.0

    for i, chunk in enumerate(retrieved_chunks, start=1):

        print(
            f"CHUNK {i}:",
            chunk.get("text", "")[:100]
        )
    if not retrieved_chunks:
        add_unanswered_question(
            question=question,
            language=language,
            reason=NOT_FOUND_MESSAGE,
            document_id=document_id,
        )
        cross_topic_search = {
            "enabled": True,
            "primary_topic": topic,
            "searched_topics": list({
                source["topic"]
                for source in retrieved_sources
                if source.get("topic")
            })
        }
        log_final_summary(
            retrieval_time=time.perf_counter() - retrieval_start_time,
            retrieved_chunks=retrieved_chunks,
        )
        return {
            "answer": NOT_FOUND_MESSAGE,
            "subject": subject,
            "topic": topic,
            "document_id": document_id,
            "retrieved_sources": retrieved_sources,
            "cross_topic_search": cross_topic_search,
            "retrieval_trace": retrieval_trace,
            "confidence": confidence,
            "source": "rag",
        }
    context = build_context(
        retrieved_chunks
    )
    prompt = f"""
CONVERSATION HISTORY:
{conversation_history}
CONTEXT:
{context}
CURRENT QUESTION:
{retrieval_question}
Rules:
- Use ONLY the supplied context for factual information.
- Use conversation history ONLY to resolve references like he, she, they, it, this, that, then, next, after that, uske baad, phir, fir, woh, usne, use.
- Never answer using conversation history alone.
- Read the entire context before answering.
- Generate the answer in English only.
- Maximum 2 concise sentences.
- Do not invent information.
- Base the answer only on the supplied context.
- If the answer can be determined by combining multiple retrieved passages, do so.
- Do not require the answer to appear as one exact sentence.
- Return exactly "Information not found in the provided content." only when the retrieved context genuinely does not contain enough information to answer.
"""
    print("PROMPT READY")
    try:
        print("FINAL RETRIEVAL QUESTION:", retrieval_question)
        print("ACTIVE DOCUMENT:", document_id)
        print("ACTIVE SUBJECT:", subject)
        print("ACTIVE TOPIC:", topic)
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.LLM_MODEL,
            input=prompt
        )
        answer = clean_answer(
            getattr(response, "output_text", "")
        )
        if is_bad_answer(answer) and retrieved_chunks:
            retry_prompt = prompt + "\n\nThe previous answer incorrectly claimed the information was unavailable. Re-read the entire context carefully and answer if the information exists anywhere in the retrieved passages."
            retry_response = await asyncio.to_thread(
                client.responses.create,
                model=settings.LLM_MODEL,
                input=retry_prompt
            )
            answer = clean_answer(
                getattr(retry_response, "output_text", "")
            )
        if answer == NOT_FOUND_MESSAGE:
            cross_topic_search = {
                "enabled": True,
                "primary_topic": topic,
                "searched_topics": list({
                    source["topic"]
                    for source in retrieved_sources
                    if source.get("topic")
                })
            }
            log_final_summary(
                retrieval_time=time.perf_counter() - retrieval_start_time,
                retrieved_chunks=retrieved_chunks,
            )
            return {
                "answer": NOT_FOUND_MESSAGE,
                "subject": subject,
                "topic": topic,
                "document_id": document_id,
                "retrieved_sources": retrieved_sources,
                "cross_topic_search": cross_topic_search,
                "retrieval_trace": retrieval_trace,
                "confidence": confidence,
                "source": "rag",
            }
        # Insert learning_state follow-up logic here
        if learning_state:
            last_topic = learning_state.get("last_topic")
            follow_up_asked = learning_state.get("follow_up_asked")

            active_document = {
                "document_id": document_id,
                "subject": subject,
                "topic": topic,
            }

            if (
                active_document
                and last_topic
                and active_document["topic"] != last_topic
                and not follow_up_asked
            ):
                answer += (
                    f"\n\nBefore we move on, are you clear with {last_topic}, or would you like me to explain it in another way?"
                )

                conversation_id = get_active_conversation(
                    user_id,
                    document_id=active_document.get("document_id"),
                    subject=active_document.get("subject"),
                    topic=active_document.get("topic"),
                )
                mark_topic_understood(
                    conversation_id
                )
        print(
            "GENERATED ANSWER:",
            answer
        )
    except Exception as e:
        print(
            "ANSWER ERROR:",
            e
        )
        import traceback
        traceback.print_exc()
        answer = NOT_FOUND_MESSAGE
    if not answer:
        answer = NOT_FOUND_MESSAGE
    if answer == NOT_FOUND_MESSAGE:
        add_unanswered_question(
            question=question,
            language=language,
            reason=NOT_FOUND_MESSAGE,
            document_id=document_id,
        )
    if (
        answer != NOT_FOUND_MESSAGE
        and not is_bad_answer(
            answer
        )
    ):
        set_cached_answer(
            normalized_question,
            answer,
            user_id=user_id,
            document_id=document_id,
        )
    cross_topic_search = {
        "enabled": True,
        "primary_topic": topic,
        "searched_topics": list({
            source["topic"]
            for source in retrieved_sources
            if source.get("topic")
        })
    }
    log_final_summary(
        retrieval_time=time.perf_counter() - retrieval_start_time,
        retrieved_chunks=retrieved_chunks,
    )
    return {
        "answer": answer,
        "subject": subject,
        "topic": topic,
        "document_id": document_id,
        "retrieved_sources": retrieved_sources,
        "cross_topic_search": cross_topic_search,
        "retrieval_trace": retrieval_trace,
        "confidence": confidence,
        "source": "rag",
    }
def check_fast_answer(
    question,
    user_id
):
    translated_question = translate_to_english(
        question
    )
    normalized_question = normalize_question(
        translated_question
    )
    qa_answer = get_similar_qa_answer(
        normalized_question
    )
    if (
        qa_answer
        and not is_bad_answer(
            qa_answer
        )
    ):
        latest_document = get_latest_document()
        document_id = latest_document.get("document_id") if latest_document else None

        set_cached_answer(
            normalized_question,
            qa_answer,
            user_id=user_id,
            document_id=document_id,
        )
        return qa_answer
    cached_answer = get_cached_answer(
        normalized_question,
        user_id=user_id,
        document_id=document_id,
    )
    if (
        cached_answer
        and not is_bad_answer(
            cached_answer
        )
    ):
        return cached_answer
    return None
async def process_task(
    question,
    user_id,
    task_id,
    language,
    intent=Intent.KNOWLEDGE_QUESTION
):
    try:
        if intent != Intent.KNOWLEDGE_QUESTION:
            update_task(
                task_id=task_id,
                answer="Unsupported intent.",
                status="COMPLETED"
            )
            return
        # Cleanup expired tasks before processing
        from task_db import cleanup_expired_tasks
        cleanup_expired_tasks()

        latest_document = get_latest_document()
        document_id = None
        subject = None
        topic = None

        if latest_document:
            document_id = latest_document.get("document_id")
            subject = latest_document.get("subject")
            topic = latest_document.get("topic")

        learning_state = get_learning_state(
            get_active_conversation(
                user_id,
                document_id=document_id,
                subject=subject,
                topic=topic,
            )
        )
        rag_result = await run_rag_pipeline(
            question,
            user_id,
            task_id=task_id,
            language=language,
            learning_state=learning_state
        )
        answer = rag_result["answer"]
        document_id = rag_result.get("document_id") or document_id
        subject = rag_result.get("subject") or subject
        topic = rag_result.get("topic") or topic
        if not answer:
            answer = NOT_FOUND_MESSAGE
        print("PROCESS TASK LANGUAGE:", language)
        print("ENGLISH ANSWER:", answer)
        if language == "english":
            translated_answer = answer
        else:
            translated_answer = translate_answer(
                answer,
                language
            )
        print("FINAL ANSWER:", translated_answer)
        # latest_document, document_id, subject and topic were initialized above.

        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=subject,
            topic=topic,
        )

        if latest_document:
            current_topic = topic or latest_document["topic"]
            previous_topic = None

            if learning_state:
                previous_topic = learning_state.get("last_topic")

            if current_topic != previous_topic:
                reset_follow_up_for_new_topic(
                    conversation_id,
                    current_topic
                )
        save_message(
            conversation_id,
            "user",
            question
        )
        save_message(
            conversation_id,
            "assistant",
            translated_answer
        )
        should_store = (
            translated_answer
            and not is_bad_answer(
                translated_answer
            )
        )
        if should_store and intent == Intent.KNOWLEDGE_QUESTION:
            qa_question = normalize_question(
                translate_to_english(
                    question
                )
            )
            add_qa_pair(
                question=qa_question,
                answer=answer,
                document_id=document_id,
                subject=subject,
                topic=topic,
                intent=intent.value,
                qa_source="USER"
            )
            if language == "english":
                set_cached_answer(
                    qa_question,
                    answer,
                    user_id=user_id,
                    document_id=document_id,
                )
        update_task(
            task_id=task_id,
            answer=translated_answer,
            status="COMPLETED"
        )
    except Exception as e:
        print("PROCESS TASK ERROR:", e)
        update_task(
            task_id=task_id,
            answer="",
            status="FAILED"
        )
async def generate_answer(
    question,
    user_id
):
    language = detect_language(
        question
    )
    print(
        "DETECTED LANGUAGE:",
        language
    )
    intent = classify_intent(question)
    print("DETECTED INTENT:", intent.value)
    latest_document = get_latest_document()
    current_subject = (latest_document.get("subject") or "").strip().lower() if latest_document else ""

    translated_for_subject = translate_to_english(question)
    detected_subject = detect_subject(translated_for_subject)

    print("LATEST DOCUMENT SUBJECT:", current_subject)
    print("DETECTED QUESTION SUBJECT:", detected_subject)

    if (
        intent == Intent.KNOWLEDGE_QUESTION
        and is_math_question(question)
        and detected_subject != "Mathematics"
        and any(ch.isdigit() for ch in question)
    ):
        # Math questions bypass QA cache/RAG intentionally.
        result = await solve_math_question(
            question,
            language
        )
        return {
            "answer": result["answer"],
            "language": language,
            "intent": intent.value,
            "verified": result["verified"],
            "source": result["source"],
        }
    if intent == Intent.GREETING:
        greeting = "Hello! How can I help you with your studies today?"
        latest_document = get_latest_document()
        document_id = latest_document.get("document_id") if latest_document else None
        subject = latest_document.get("subject") if latest_document else None
        topic = latest_document.get("topic") if latest_document else None

        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=subject,
            topic=topic,
        )
        save_message(conversation_id, "user", question)
        # Translate greeting if language is not English
        if language != "english":
            greeting_translated = translate_answer(greeting, language)
        else:
            greeting_translated = greeting
        save_message(conversation_id, "assistant", greeting_translated)
        return {
            "answer": greeting_translated,
            "language": language,
            "intent": intent.value
        }
    elif intent == Intent.FEEDBACK:
        acknowledgement = "You're welcome! Let me know if you'd like to learn anything else."
        latest_document = get_latest_document()
        document_id = latest_document.get("document_id") if latest_document else None
        subject = latest_document.get("subject") if latest_document else None
        topic = latest_document.get("topic") if latest_document else None

        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=subject,
            topic=topic,
        )
        save_message(conversation_id, "user", question)
        # Translate acknowledgement if language is not English
        if language != "english":
            acknowledgement_translated = translate_answer(acknowledgement, language)
        else:
            acknowledgement_translated = acknowledgement
        save_message(conversation_id, "assistant", acknowledgement_translated)
        return {
            "answer": acknowledgement_translated,
            "language": language,
            "intent": intent.value
        }
    elif intent == Intent.FOLLOW_UP:
        latest_document = get_latest_document()
        document_id = latest_document.get("document_id") if latest_document else None
        subject = latest_document.get("subject") if latest_document else None
        topic = latest_document.get("topic") if latest_document else None

        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=subject,
            topic=topic,
        )
        rag_result = await run_rag_pipeline(
            question,
            user_id,
            task_id=None,
            language=language,
            learning_state=get_learning_state(conversation_id)
        )
        answer = rag_result["answer"]
        translated_answer = (
            answer
            if language == "english"
            else translate_answer(answer, language)
        )
        save_message(
            conversation_id,
            "user",
            question
        )
        save_message(conversation_id, "assistant", translated_answer)

        return {
            "answer": translated_answer,
            "language": language,
            "intent": intent.value,
            "subject": rag_result.get("subject"),
            "topic": rag_result.get("topic"),
            "document_id": rag_result.get("document_id"),
            "retrieved_sources": rag_result.get("retrieved_sources", []),
            "cross_topic_search": rag_result.get("cross_topic_search", {}),
            "retrieval_trace": rag_result.get("retrieval_trace", {}),
            "confidence": rag_result.get("confidence", 0.0),
        }
    elif intent == Intent.QUIZ:
        return {"answer": "Quiz generation will be handled here.", "language": language, "intent": intent.value}
    elif intent == Intent.SUMMARY:
        return {"answer": "Summary generation will be handled here.", "language": language, "intent": intent.value}
    elif intent == Intent.MIND_MAP:
        return {"answer": "Mind map generation will be handled here.", "language": language, "intent": intent.value}
    elif intent == Intent.ARCHITECTURE:
        return {"answer": "Architecture generation will be handled here.", "language": language, "intent": intent.value}
    elif intent == Intent.TRANSLATE:
        translated_text = translate_answer(question, language)
        latest_document = get_latest_document()
        document_id = latest_document.get("document_id") if latest_document else None
        subject = latest_document.get("subject") if latest_document else None
        topic = latest_document.get("topic") if latest_document else None
        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=subject,
            topic=topic,
        )
        save_message(conversation_id, "user", question)
        save_message(conversation_id, "assistant", translated_text)
        return {
            "answer": translated_text,
            "language": language,
            "intent": intent.value
        }
    elif intent == Intent.DELETE_TOPIC:
        latest_document = get_latest_document()
        if not latest_document:
            return {
                "answer": "No active topic found to delete.",
                "language": language,
                "intent": intent.value
            }
        document_id = latest_document["document_id"]
        delete_document_chunks(document_id)
        delete_document_qa_pairs(document_id)
        delete_document_tasks(document_id)
        delete_document_unanswered_questions(document_id)
        delete_document_upload_history(document_id)
        # Also delete conversations for the document/topic
        conversation_id = get_active_conversation(
            user_id,
            document_id=document_id,
            subject=latest_document.get("subject"),
            topic=latest_document.get("topic"),
        )
        reset_follow_up_for_new_topic(
            conversation_id,
            latest_document.get("topic")
        )
        delete_document_conversations(document_id)

        return {
            "answer": f"Topic '{latest_document['topic']}' deleted successfully.",
            "language": language,
            "intent": intent.value
        }
    elif intent == Intent.UPLOAD_TOPIC:
        # This is a placeholder for topic upload. If upload_result is available, include ingestion_summary.
        upload_result = None  # Replace with actual upload result if available in future implementation
        response = {
            "answer": "Topic upload will be handled here.",
            "language": language,
            "intent": intent.value
        }
        if upload_result:
            response["ingestion_summary"] = upload_result.get("ingestion_summary", {})
        return response

    # RAG pipeline for knowledge questions before background task creation
    if intent == Intent.KNOWLEDGE_QUESTION:
        rag_result = await run_rag_pipeline(
            question,
            user_id,
            language=language,
        )

        translated_answer = (
            rag_result["answer"]
            if language == "english"
            else translate_answer(rag_result["answer"], language)
        )

        # Store every successful RAG answer in the QA database
        try:
            add_qa_pair(
                question=normalize_question(translate_to_english(question)),
                answer=rag_result["answer"],
                document_id=get_latest_document().get("document_id") if get_latest_document() else None,
                subject=rag_result.get("subject"),
                topic=rag_result.get("topic"),
                user_id=user_id,
                source="RAG",
                verified=(rag_result.get("answer") != NOT_FOUND_MESSAGE),
                intent=intent.value,
                qa_source="USER"
            )
        except Exception as qa_exc:
            print("QA DB persistence failed:", qa_exc)

        return {
            "answer": translated_answer,
            "language": language,
            "intent": intent.value,
            "subject": rag_result.get("subject"),
            "topic": rag_result.get("topic"),
            "document_id": rag_result.get("document_id"),
            "retrieved_sources": rag_result.get("retrieved_sources", []),
            "cross_topic_search": rag_result.get("cross_topic_search", {}),
            "retrieval_trace": rag_result.get("retrieval_trace", {}),
            "confidence": rag_result.get("confidence", 0.0),
            "verified": rag_result.get("answer") != NOT_FOUND_MESSAGE,
            "source": "rag",
        }
    latest_document = get_latest_document()
    document_id = latest_document.get("document_id") if latest_document else None
    subject = latest_document.get("subject") if latest_document else None
    topic = latest_document.get("topic") if latest_document else None
    conversation_id = get_active_conversation(
        user_id,
        document_id=document_id,
        subject=subject,
        topic=topic,
    )
    task_id = create_task(
        question=question,
        language=language,
        user_id=user_id,
        conversation_id=conversation_id,
        source_type="text",
        document_id=document_id,
        subject=subject,
        topic=topic,
    )
    # Start the processing task with intent in a background thread
    assert task_id is not None
    import threading
    if intent == Intent.KNOWLEDGE_QUESTION:
        threading.Thread(
            target=lambda: asyncio.run(
                process_task(
                    question,
                    user_id,
                    task_id,
                    language,
                    intent=intent,
                )
            ),
            daemon=True,
        ).start()
    return {
        "task_id": task_id,
        "language": language,
        "intent": intent.value
    }


# --- /ask endpoint handler ---
from fastapi import APIRouter, Depends
from fastapi import Request
from fastapi import Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# Define request model for /ask endpoint as per existing usage
class AskRequest(BaseModel):
    question: str
    user_id: str

@app.post("/ask")
async def ask_endpoint(request: AskRequest):
    # Always call the generate_answer async function
    result = await generate_answer(question=request.question, user_id=request.user_id)
    return result

# --- Subject-specific ask endpoints ---
from fastapi import status
from fastapi.responses import JSONResponse

async def _generate_subject_answer(request: AskRequest, subject: str):
    """
    Helper to call the existing answer-generation flow but force the subject.
    """
    # We'll use the same generate_answer logic, but monkey-patch get_latest_document to return the forced subject.
    # This avoids duplicating retrieval/answer-generation logic.
    # Save the original get_latest_document
    from qa_db import get_similar_qa_answer  # to avoid shadowing
    import backend.main as main_mod
    orig_get_latest_document = main_mod.get_latest_document
    def mock_latest_document():
        doc = orig_get_latest_document()
        # Always set the subject to the forced one
        if doc:
            doc = dict(doc)
            doc["subject"] = subject
            return doc
        else:
            return {"subject": subject, "document_id": None, "topic": None}
    main_mod.get_latest_document = mock_latest_document
    try:
        result = await generate_answer(question=request.question, user_id=request.user_id)
    finally:
        main_mod.get_latest_document = orig_get_latest_document
    return result
@app.post("/physics/ask")
async def physics_ask_endpoint(request: AskRequest):
    return await _generate_subject_answer(request, subject="Physics")
@app.post("/mathematics/ask")
async def mathematics_ask_endpoint(request: AskRequest):
    return await _generate_subject_answer(request, subject="Mathematics")
@app.post("/chemistry/ask")
async def chemistry_ask_endpoint(request: AskRequest):
    return await _generate_subject_answer(request, subject="Chemistry")
@app.post("/biology/ask")
async def biology_ask_endpoint(request: AskRequest):
    return await _generate_subject_answer(request, subject="Biology")