from dotenv import load_dotenv
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

REQUIRED_ENV_VARS = (
    "POSTGRES_HOST",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "OPENAI_API_KEY",
    "ASSEMBLYAI_API_KEY"
)


class Settings:

    POSTGRES_HOST = os.getenv(
        "POSTGRES_HOST"
    )

    POSTGRES_PORT = int(
        os.getenv(
            "POSTGRES_PORT",
            5432
        )
    )

    POSTGRES_DB = os.getenv(
        "POSTGRES_DB"
    )

    POSTGRES_USER = os.getenv(
        "POSTGRES_USER"
    )

    POSTGRES_PASSWORD = os.getenv(
        "POSTGRES_PASSWORD"
    )

    REDIS_HOST = os.getenv(
        "REDIS_HOST"
    )

    REDIS_PORT = int(
        os.getenv(
            "REDIS_PORT",
            6379
        )
    )

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY"
    )

    ASSEMBLYAI_API_KEY = os.getenv(
        "ASSEMBLYAI_API_KEY"
    )

    LLM_MODEL = os.getenv(
        "LLM_MODEL",
        "gpt-5-nano"
    )

    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "text-embedding-3-small"
    )

    TOP_K = int(
        os.getenv(
            "TOP_K",
            30
        )
    )

    FINAL_CONTEXT_CHUNKS = int(
        os.getenv(
            "FINAL_CONTEXT_CHUNKS",
            15
        )
    )

    CONFIDENCE_THRESHOLD = float(
        os.getenv(
            "CONFIDENCE_THRESHOLD",
            0.35
        )
    )

    QA_THRESHOLD = float(
        os.getenv(
            "QA_THRESHOLD",
            0.85
        )
    )

    QA_SIMILARITY_THRESHOLD = float(
        os.getenv(
            "QA_SIMILARITY_THRESHOLD",
            0.90
        )
    )

    CHUNK_SIZE = int(
        os.getenv(
            "CHUNK_SIZE",
            400
        )
    )

    CHUNK_OVERLAP = int(
        os.getenv(
            "CHUNK_OVERLAP",
            50
        )
    )

    REQUEST_TIMEOUT = int(
        os.getenv(
            "REQUEST_TIMEOUT",
            300
        )
    )

    MAX_PARALLEL_REQUESTS = int(
        os.getenv(
            "MAX_PARALLEL_REQUESTS",
            20
        )
    )

    MAX_WORKERS = int(
        os.getenv(
            "MAX_WORKERS",
            50
        )
    )

    CACHE_TTL = int(
        os.getenv(
            "CACHE_TTL",
            3600
        )
    )
    CONVERSATION_RETENTION_HOURS = int(
        os.getenv(
            "CONVERSATION_RETENTION_HOURS",
            3
        )
    )
    MAX_CONVERSATION_MESSAGES = int(
        os.getenv(
            "MAX_CONVERSATION_MESSAGES",
            5
        )
    )
    TASK_RETENTION_HOURS = int(
        os.getenv(
            "TASK_RETENTION_HOURS",
            3
        )
    )
    SUPPORTED_LANGUAGES = [
        "english",
        "hindi",
        "hinglish"
    ]
    VOICE_SUPPORTED_LANGUAGES = [
        "english",
        "hindi",
        "hinglish"
    ]

    @classmethod
    def validate(cls):
        missing = [
            key for key in REQUIRED_ENV_VARS
            if not os.getenv(key)
        ]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

Settings.validate()
settings = Settings()