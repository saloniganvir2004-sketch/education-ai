import os
import time
import traceback

import assemblyai as aai

from config import settings


print("LOADING TRANSCRIBER")

print(
    "ASSEMBLY API KEY EXISTS:",
    bool(settings.ASSEMBLYAI_API_KEY)
)

aai.settings.api_key = (
    settings.ASSEMBLYAI_API_KEY
)

print("ASSEMBLY API KEY SET")

transcriber = aai.Transcriber()

print("TRANSCRIBER CREATED")


def transcribe_audio(
    file_path
):

    print(
        "ASSEMBLYAI TRANSCRIPTION START"
    )

    print(
        "FILE PATH:",
        file_path
    )

    print(
        "FILE EXISTS:",
        os.path.exists(file_path)
    )

    config = aai.TranscriptionConfig(
        language_detection=True
    )

    for attempt in range(1, 4):

        try:

            print(
                f"SENDING TO ASSEMBLYAI ATTEMPT {attempt}"
            )

            start_time = time.time()

            transcript = transcriber.transcribe(
                file_path,
                config=config
            )

            print(
                "RESPONSE RECEIVED"
            )

            print(
                "TIME TAKEN:",
                round(
                    time.time() - start_time,
                    2
                ),
                "SECONDS"
            )

            print(
                "ASSEMBLYAI TRANSCRIPTION FINISHED"
            )

            print(
                "STATUS:",
                transcript.status
            )

            if transcript.status == "error":

                raise Exception(
                    transcript.error
                )

            detected_language = str(
                getattr(
                    transcript,
                    "language_code",
                    ""
                )
                or ""
            ).lower()

            if detected_language.startswith(
                "hi"
            ):

                language = "hindi"

            elif detected_language.startswith(
                "en"
            ):

                language = "english"

            else:

                language = "hinglish"

            return {
                "text": str(
                    transcript.text or ""
                ).strip(),
                "language": language
            }

        except Exception as e:

            print(
                f"ASSEMBLYAI ERROR ATTEMPT {attempt}:",
                repr(e)
            )

            traceback.print_exc()

            if attempt == 3:

                raise

            time.sleep(5)

    raise Exception(
        "AssemblyAI transcription failed after 3 attempts"
    )


def validate_audio_transcription(
    file_path
):

    result = transcribe_audio(
        file_path
    )

    return {
        "valid": bool(
            result["text"]
        ),
        "length": len(
            result["text"]
        ),
        "text": result["text"],
        "language": result[
            "language"
        ]
    }


def transcribe_video(
    file_path
):

    return transcribe_audio(
        file_path
    )