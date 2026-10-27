"""Extract plain text from uploaded resume files."""

import io
import re

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".txt")


class UnsupportedFileError(ValueError):
    pass


def extract_text(filename: str, data: bytes) -> str:
    """Return the cleaned text content of a PDF, DOCX or TXT file."""
    name = filename.lower()

    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif name.endswith(".docx"):
        document = Document(io.BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    elif name.endswith(".txt"):
        text = data.decode("utf-8", errors="ignore")
    else:
        raise UnsupportedFileError(
            f"{filename}: only {', '.join(SUPPORTED_EXTENSIONS)} files are supported"
        )

    return clean_text(text)


def clean_text(text: str) -> str:
    """Collapse whitespace so the text is easier to tokenize."""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()
