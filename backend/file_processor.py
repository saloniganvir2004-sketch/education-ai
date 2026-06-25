from pypdf import PdfReader
from docx import Document
import textract
from PIL import Image

import pytesseract
from pdf2image import convert_from_path

from transcriber import (
    transcribe_audio,
    transcribe_video
)

import re


SUPPORTED_LANGUAGES = [
    "english",
    "hindi",
    "hinglish"
]


def clean_text(text):

    if not text:
        return ""

    text = str(text)

    text = text.replace("\x00", " ")

    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\r", "\n", text)

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def detect_content_language(text):

    text = str(text)
    if not text.strip():
        return "english"

    hindi_chars = sum(
        1
        for c in text
        if "\u0900" <= c <= "\u097F"
    )

    english_chars = sum(
        1
        for c in text
        if c.isascii() and c.isalpha()
    )

    if (
        hindi_chars > 0
        and english_chars > 0
    ):
        return "hinglish"

    if hindi_chars > english_chars:
        return "hindi"

    return "english"


def ocr_pdf(file_path):

    try:
        pages = convert_from_path(
            file_path,
            dpi=300
        )

        text = ""
        page_data = []
        cumulative_chars = 0

        for page_number, page in enumerate(pages, start=1):
            page_text = pytesseract.image_to_string(
                page,
                lang="eng+hin"
            )
            page_text = clean_text(page_text)
            start_char = cumulative_chars

            text += page_text + "\n"

            end_char = start_char + len(page_text)
            cumulative_chars = len(text)

            char_count = len(page_text)
            page_data.append({
                "page": page_number,
                "text": page_text,
                "char_count": char_count,
                "start_char": start_char,
                "end_char": end_char,
            })
            print(
                f"PAGE {page_number} | "
                f"START={start_char} | "
                f"END={end_char} | "
                f"CHARS={char_count}"
            )

        return {
            "text": clean_text(text),
            "pages": page_data,
        }
    except Exception as e:
        print("OCR PDF ERROR:")
        print(e)
        return {
            "text": "",
            "pages": [],
        }


def process_pdf(file_path):

    print("PROCESS_PDF START")

    text = ""
    pages = []
    cumulative_chars = 0

    try:
        pdf = PdfReader(file_path)
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)
            if page_text:
                start_char = cumulative_chars

                text += page_text + "\n"

                end_char = start_char + len(page_text)
                cumulative_chars = len(text)

                char_count = len(page_text)

                pages.append({
                    "page": page_number,
                    "text": page_text,
                    "char_count": char_count,
                    "start_char": start_char,
                    "end_char": end_char,
                })
                print(
                    f"PAGE {page_number} | "
                    f"START={start_char} | "
                    f"END={end_char} | "
                    f"CHARS={char_count}"
                )

    except Exception as e:

        print(
            "PDF EXTRACTION ERROR:",
            e
        )

        text = ""

    if len(text.strip()) < 100:
        print(
            "SCANNED PDF DETECTED - USING OCR"
        )
        ocr_result = ocr_pdf(
            file_path
        )
        text = ocr_result.get("text", "")
        pages = ocr_result.get("pages", [])

    text = clean_text(
        text
    )

    print(
        "PROCESS_PDF END"
    )

    # Returns extracted pages for upload pipeline persistence.
    return {
        "text": text,
        "language": detect_content_language(
            text
        ),
        "pages": pages,
    }


def process_docx(file_path):

    print("PROCESS_DOCX START")
    try:
        doc = Document(
            file_path
        )

        text = "\n".join(
            paragraph.text
            for paragraph in doc.paragraphs
        )

        text = clean_text(
            text
        )

        print(
            "PROCESS_DOCX END"
        )

        return {
            "text": text,
            "language": detect_content_language(
                text
            ),
            "pages": [],
        }
    except Exception as e:
        print("DOCX PROCESS ERROR:", e)
        return {"text": "", "language": "english", "pages": []}


def process_doc(file_path):

    print("PROCESS_DOC START")
    try:
        text = textract.process(file_path).decode("utf-8", errors="ignore")

        text = clean_text(text)

        print("PROCESS_DOC END")

        return {
            "text": text,
            "language": detect_content_language(text),
            "pages": [],
        }
    except Exception as e:
        print("DOC PROCESS ERROR:", e)
        return {"text": "", "language": "english", "pages": []}


def process_txt(file_path):

    print("PROCESS_TXT START")
    try:
        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:
            text = file.read()

        text = clean_text(
            text
        )

        print(
            "PROCESS_TXT END"
        )

        return {
            "text": text,
            "language": detect_content_language(
                text
            ),
            "pages": [],
        }
    except Exception as e:
        print("TXT PROCESS ERROR:", e)
        return {"text": "", "language": "english", "pages": []}


def process_image(file_path):

    print("PROCESS_IMAGE START")
    try:
        image = Image.open(
            file_path
        )

        text = pytesseract.image_to_string(
            image,
            lang="eng+hin"
        )

        text = clean_text(
            text
        )

        print(
            "PROCESS_IMAGE END"
        )

        return {
            "text": text,
            "language": detect_content_language(
                text
            ),
            "pages": [
                {
                    "page": 1,
                    "text": text,
                    "char_count": len(text),
                    "start_char": 0,
                    "end_char": len(text),
                }
            ],
        }
    except Exception as e:
        print("IMAGE PROCESS ERROR:", e)
        return {"text": "", "language": "english", "pages": []}


def process_audio(file_path):

    print(
        "PROCESS_AUDIO START"
    )

    result = transcribe_audio(
        file_path
    )

    text = clean_text(
        result.get("text", "")
    )

    language = str(
        result.get(
            "language",
            "english"
        )
    ).lower()

    if language not in SUPPORTED_LANGUAGES:

        language = detect_content_language(
            text
        )

    print(
        "PROCESS_AUDIO END"
    )

    return {
        "text": text,
        "language": language,
        "pages": [],
    }


def process_video(file_path):

    print(
        "PROCESS_VIDEO START"
    )

    result = transcribe_video(
        file_path
    )

    text = clean_text(
        result.get("text", "")
    )

    language = str(
        result.get(
            "language",
            "english"
        )
    ).lower()

    if language not in SUPPORTED_LANGUAGES:

        language = detect_content_language(
            text
        )

    print(
        "PROCESS_VIDEO END"
    )

    return {
        "text": text,
        "language": language,
        "pages": [],
    }


def process_file(file_path):

    print(
        "PROCESS_FILE:",
        file_path
    )

    lower_path = file_path.lower()
    if not file_path:
        raise ValueError("Empty file path provided.")

    if lower_path.endswith(".pdf"):

        return process_pdf(
            file_path
        )

    if lower_path.endswith(".docx"):

        return process_docx(
            file_path
        )

    if lower_path.endswith(".doc"):

        return process_doc(
            file_path
        )

    if lower_path.endswith(".txt"):

        return process_txt(
            file_path
        )

    if (
        lower_path.endswith(".png")
        or lower_path.endswith(".jpg")
        or lower_path.endswith(".jpeg")
        or lower_path.endswith(".bmp")
        or lower_path.endswith(".tiff")
        or lower_path.endswith(".webp")
    ):

        return process_image(
            file_path
        )

    if (
        lower_path.endswith(".mp3")
        or lower_path.endswith(".wav")
        or lower_path.endswith(".m4a")
    ):

        return process_audio(
            file_path
        )

    if (
        lower_path.endswith(".mp4")
        or lower_path.endswith(".mov")
        or lower_path.endswith(".avi")
    ):

        return process_video(
            file_path
        )

    raise ValueError(
        f"Unsupported file format: {file_path}"
    )