import re
from enum import Enum


class Intent(str, Enum):
    KNOWLEDGE_QUESTION = "KNOWLEDGE_QUESTION"
    FOLLOW_UP = "FOLLOW_UP"
    FEEDBACK = "FEEDBACK"
    GREETING = "GREETING"
    QUIZ = "QUIZ"
    SUMMARY = "SUMMARY"
    MIND_MAP = "MIND_MAP"
    ARCHITECTURE = "ARCHITECTURE"
    TRANSLATE = "TRANSLATE"
    DELETE_TOPIC = "DELETE_TOPIC"
    UPLOAD_TOPIC = "UPLOAD_TOPIC"


GREETING_PATTERNS = {
    "hi",
    "hello",
    "hey",
    "heyy",
    "heyyy",
    "namaste",
    "good morning",
    "good afternoon",
    "good evening",
    "hii",
    "yo",
    "what you doing"
}

FEEDBACK_PATTERNS = {
    "ok",
    "okay",
    "thanks",
    "thank you",
    "thankyou",
    "nice",
    "good",
    "great",
    "awesome",
    "perfect",
    "cool",
    "understood",
    "got it",
    "i understood",
    "samajh gaya",
    "samajh gayi",
    "acha",
    "accha",
    "well done",
    "helpful",
    "fine"
}

FOLLOW_UP_PATTERNS = {
    "tell me more",
    "more",
    "continue",
    "go on",
    "next",
    "then",
    "what next",
    "and then",
    "what happened next",
    "what happened then",
    "explain again",
    "again",
    "simplify",
    "simple words",
    "in simple words",
    "aur batao",
    "aur",
    "phir",
    "phir kya hua",
    "continue please",
    "more details",
    "elaborate",
    "give more details"
}

COMMAND_PATTERNS = {
    Intent.QUIZ: {"quiz", "generate quiz"},
    Intent.SUMMARY: {"summary", "generate summary"},
    Intent.MIND_MAP: {"mind map", "generate mind map"},
    Intent.ARCHITECTURE: {"architecture", "generate architecture"},
    Intent.TRANSLATE: {"translate", "translate answer"},
    Intent.DELETE_TOPIC: {"delete topic", "delete file", "delete document"},
    Intent.UPLOAD_TOPIC: {"upload", "upload topic", "replace topic", "replace file"},
}

QUESTION_WORDS = {
    "what",
    "why",
    "how",
    "when",
    "where",
    "which",
    "who",
    "whose",
    "whom",
    "define",
    "describe",
    "explain",
    "difference",
    "compare",
    "formula",
    "meaning",
    "purpose",
    "uses",
    "advantages",
    "disadvantages"
}


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"([a-z])\1{2,}", r"\1\1", text)
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def contains_any(text: str, patterns) -> bool:
    normalized = normalize_text(text)
    return any(normalized == normalize_text(pattern) for pattern in patterns)


def is_question(text: str) -> bool:
    if "?" in text:
        return True

    words = text.split()

    if not words:
        return False

    if words[0] in QUESTION_WORDS:
        return True

    return False


def classify_intent(message: str) -> Intent:
    if not message:
        return Intent.GREETING

    text = normalize_text(message)

    if contains_any(text, GREETING_PATTERNS):
        return Intent.GREETING

    if contains_any(text, FEEDBACK_PATTERNS):
        return Intent.FEEDBACK

    if is_question(text):
        return Intent.KNOWLEDGE_QUESTION

    normalized_follow_ups = {
        normalize_text(pattern)
        for pattern in FOLLOW_UP_PATTERNS
    }
    if text in normalized_follow_ups:
        return Intent.FOLLOW_UP

    for command_intent, patterns in COMMAND_PATTERNS.items():
        if contains_any(text, patterns):
            return command_intent

    return Intent.KNOWLEDGE_QUESTION