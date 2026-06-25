from fastapi import FastAPI, BackgroundTasks, Form
from fastapi import UploadFile
from fastapi import File
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from routes.document_routes import router as document_router
from routes.subject_routes import router as subject_router
from routes.qa_routes import router as qa_router
from chat_api import (
    ChatRequest,
    ChatResponse,
    ChatRequestV2,
    ChatResponseV2,
    ChatContext,
    ChatMetadata,
    ChatSource
)

from schemas import (
    QuestionRequest,
    HealthResponse,
    AskResponse,
    CompareRequest,
    VoiceResponse,
    UpdateQARequest,
    CreateQARequest
)

from main import generate_answer

from upload_api import (
    process_uploaded_file
)

from voice_api import (
    process_voice_question
)

from quiz_generator import generate_quiz
from summary_generator import generate_summary
from mindmap_generator import generate_mindmap
from architecture_generator import generate_architecture

from task_db import (
    get_all_tasks,
    get_task
)

# Add DB connection import
from database import get_db_connection

# --- Cascade delete imports ---
from vector_store import delete_document_chunks
from qa_db import delete_document_qa_pairs
from upload_history_db import delete_document_upload_history
from task_db import delete_document_tasks
from conversation_db import delete_document_conversations

from upload_history_db import (
    get_uploaded_files
)
from upload_history_db import topic_exists

from unanswered_db import (
    get_unanswered_questions,
    delete_unanswered_question,
    delete_document_unanswered_questions
)

from compare_db import (
    compare_answer
)

from document_registry_api import (
    router as document_registry_router
)


from qa_crud import (
    get_all_qa_pairs,
    get_qa_pair_by_id,
    update_qa_pair,
    delete_qa_pair,
    add_qa_pair
)

app = FastAPI(
    title="Education AI API",
    version="3.0"
)


# Legacy document registry router disabled after document API consolidation
# app.include_router(
#     document_registry_router
# )

app.include_router(
    document_router,
    prefix="/documents",
    tags=["Documents"]
)

app.include_router(subject_router)

app.include_router(
    qa_router,
    prefix="/qa",
    tags=["QA Management"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_backend_user_id(
    request: Request
):

    user_id = request.headers.get(
        "X-User-Id"
    )

    if not user_id:

        user_id = "demo-user"

    return user_id


@app.get("/")
def home():

    return {
        "message": "Education AI API Running",
        "status": "healthy"
    }


@app.get(
    "/health",
    response_model=HealthResponse
)
def health():

    return {
        "status": "healthy"
    }


@app.post(
    "/ask",
    response_model=AskResponse
)
async def ask(
    background_tasks: BackgroundTasks,
    request: Request,
    body: QuestionRequest
):

    user_id = get_backend_user_id(
        request
    )

    result = await generate_answer(
        question=body.question,
        user_id=user_id
    )
    print("API RESULT:", result)


    return result


@app.post(
    "/ask-voice",
    response_model=VoiceResponse
)
async def ask_voice(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...)
):

    user_id = get_backend_user_id(
        request
    )

    return await process_voice_question(
        file=file,
        user_id=user_id,
        background_tasks=background_tasks
    )


@app.post("/compare")
def compare(
    request: CompareRequest
):
    # Validate that question and answer are non-empty after stripping whitespace
    if not request.question.strip() or not request.answer.strip():
        return {
            "status": "INVALID_REQUEST",
            "message": "Question and answer are required."
        }
    return compare_answer(
        request.question,
        request.answer
    )


@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    subject: str = Form(""),
    topic: str = Form("")
):
    subject = subject.strip()
    topic = topic.strip()
    return await process_uploaded_file(
        file=file,
        subject=subject,
        topic=topic
    )


@app.get("/task/{task_id}")
def task_status(
    task_id: str
):

    task = get_task(
        task_id
    )

    if not task:

        return {
            "task_id": task_id,
            "status": "NOT_FOUND"
        }

    return {
        "task_id": task[0],
        "question": task[3],
        "answer": task[4],
        "language": task[5],
        "status": task[6],
        "confidence": task[8],
        "document_id": task[9],
        "subject": task[10],
        "topic": task[11]
    }


@app.get("/answer/{task_id}")
def get_answer(
    task_id: str
):

    task = get_task(
        task_id
    )

    if not task:

        return {
            "task_id": task_id,
            "status": "NOT_FOUND"
        }

    return {
        "task_id": task[0],
        "question": task[3],
        "answer": task[4],
        "language": task[5],
        "status": task[6],
        "confidence": task[8],
        "document_id": task[9],
        "subject": task[10],
        "topic": task[11]
    }


@app.get("/tasks")
def get_tasks():

    return {
        "tasks": get_all_tasks()
    }


@app.get("/uploads")
def get_uploads():

    return {
        "uploads": get_uploaded_files()
    }


# --- Check if topic exists endpoint ---
@app.get("/topics/exists")
def check_topic_exists(subject: str, topic: str):
    return {
        "exists": topic_exists(
            subject.strip(),
            topic.strip()
        )
    }

@app.get("/unanswered")
def get_unanswered():

    return {
        "unanswered": get_unanswered_questions()
    }


@app.delete(
    "/unanswered/{question_id}"
)
def delete_unanswered(
    question_id: int
):
    delete_unanswered_question(
        question_id
    )
    return {
        "status": "deleted",
        "question_id": question_id
    }


@app.get("/generate-quiz")
def generate_quiz_api():

    return generate_quiz()


@app.get("/generate-summary")
def generate_summary_api():

    return generate_summary()


@app.get("/generate-mindmap")
def generate_mindmap_api():

    return generate_mindmap()


@app.get("/generate-architecture")
def generate_architecture_api():

    return generate_architecture()



# --- Document Cascade Delete Endpoint ---

@app.delete("/document/{document_id}/cascade")
def cascade_delete_document(document_id: str):
    connection = get_db_connection()
    try:
        connection.autocommit = False

        delete_document_chunks(document_id)
        delete_document_qa_pairs(document_id)
        delete_document_tasks(document_id)
        delete_document_unanswered_questions(document_id)
        delete_document_upload_history(document_id)
        delete_document_conversations(document_id)

        connection.commit()

        return {
            "status": "DELETED",
            "document_id": document_id
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

# --- QA PAIRS ENDPOINTS ---

@app.post("/qa-pair")
def create_qa(body: CreateQARequest):
    qa = add_qa_pair(
        body.question,
        body.answer
    )
    return {
        "status": "CREATED",
        "id": qa[0],
        "question": qa[1],
        "answer": qa[2]
    }

@app.get("/qa-pairs")
def qa_pairs():
    qa_pairs = get_all_qa_pairs()

    return {
        "count": len(qa_pairs),
        "qa_pairs": qa_pairs
    }


@app.get("/qa-pair/{qa_id}")
def qa_pair(qa_id: int):
    qa = get_qa_pair_by_id(qa_id)

    if not qa:
        return {
            "status": "NOT_FOUND"
        }

    return {
        "id": qa[0],
        "question": qa[1],
        "answer": qa[2]
    }


@app.put("/qa-pair/{qa_id}")
def update_qa(qa_id: int, body: UpdateQARequest):
    updated = update_qa_pair(
        qa_id,
        body.question,
        body.answer
    )

    if not updated:
        return {
            "status": "NOT_FOUND"
        }

    qa = get_qa_pair_by_id(qa_id)

    return {
        "status": "UPDATED",
        "id": qa[0],
        "question": qa[1],
        "answer": qa[2]
    }


@app.delete("/qa-pair/{qa_id}")
def delete_qa(qa_id: int):
    deleted = delete_qa_pair(qa_id)

    if not deleted:
        return {
            "status": "NOT_FOUND"
        }

    return {
        "status": "DELETED",
        "id": qa_id
    }
@app.post(
    "/chat",
    response_model=ChatResponseV2
)
async def chat(request: ChatRequestV2):
    result = await generate_answer(
        question=request.question,
        user_id=(
            request.metadata.user_id
            if request.metadata
            else None
        ),
    )
    if "confidence" not in result or result.get("confidence") is None:
        result["confidence"] = 0.0

    return ChatResponseV2(
        answer=result.get("answer"),
        source=result.get("source"),
        confidence=float(result.get("confidence") or 0.0),
        context=ChatContext(
            subject=request.context.subject,
            topic=request.context.topic
        ) if request.context else None,
        metadata=request.metadata,
        retrieval_source=ChatSource(
            subject=result.get("subject"),
            topic=result.get("topic"),
            document_id=(
                result.get("document_id")
                or result.get("retrieval_source", {}).get("document_id")
            )
        )
    )