import os
import uuid

from fastapi import UploadFile, BackgroundTasks

from transcriber import (
    transcribe_audio
)

from main import (
    generate_answer,
    process_task
)

from answer_translator import (
    translate_answer
)


UPLOAD_FOLDER = "../uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


async def process_voice_question(
    file: UploadFile,
    user_id: str,
    background_tasks: BackgroundTasks
):

    filename = (
        f"{uuid.uuid4()}_{file.filename}"
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            await file.read()
        )

    transcript_result = (
        transcribe_audio(
            file_path
        )
    )

    transcript = transcript_result.get(
        "text",
        ""
    ).strip()

    language = transcript_result.get(
        "language",
        "english"
    )

    if not transcript:
        return {
            "task_id": None,
            "transcript": "",
            "language": language,
            "answer": "Unable to transcribe the audio."
        }

    result = generate_answer(
        question=transcript,
        user_id=user_id
    )
    if "answer" in result:

        translated_answer = (
            result["answer"]
            if language == "english"
            else translate_answer(
                result["answer"],
                language
            )
        )

        return {
            "task_id": None,
            "transcript": transcript,
            "language": language,
            "answer": translated_answer
        }

    background_tasks.add_task(
        process_task,
        transcript,
        user_id,
        result["task_id"],
        language
    )

    return {

        "task_id": result["task_id"],

        "transcript": transcript,

        "language": language

    }