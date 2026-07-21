import os
import re
import uuid
from urllib.parse import quote
from typing import Optional

from werkzeug.utils import secure_filename

IMAGE_KEYWORDS = [
    "generate",
    "create",
    "draw",
    "paint",
    "illustrate",
    "design",
    "image",
    "picture",
]

STOP_WORDS = [
    "an",
    "a",
    "the",
    "of",
    "for",
    "please",
    "with",
    "in",
    "on",
    "to",
    "and",
    "me",
]

ALLOWED_FILE_EXTENSIONS = {"pdf", "docx", "txt", "csv"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}


def is_image_prompt(text: str) -> bool:
    """Return True when the user message appears to request image generation."""
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in IMAGE_KEYWORDS)


def clean_image_prompt(text: str) -> str:
    """Remove image-action keywords and stop words from the prompt."""
    lower = text.lower()
    lower = re.sub(r"[^a-z0-9\s]", " ", lower)
    lower = re.sub(
        r"\b(" + r"|".join(re.escape(k) for k in IMAGE_KEYWORDS) + r")\b",
        "",
        lower,
    )
    lower = re.sub(
        r"\b(" + r"|".join(re.escape(k) for k in STOP_WORDS) + r")\b",
        "",
        lower,
    )
    prompt = " ".join(lower.split()).strip()
    return prompt or text.strip()


def build_pollinations_url(prompt: str) -> str:
    """Create a safe URL for the legacy Pollinations image generation endpoint."""
    return f"https://image.pollinations.ai/prompt/{quote(prompt)}"


def allowed_file(filename: str, allowed_ext: set[str]) -> bool:
    """Check whether the uploaded filename uses an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_ext


def extract_text_from_file(filepath: str, filename: str) -> Optional[str]:
    """Extract text from common document types for uploaded files."""
    ext = filename.rsplit(".", 1)[1].lower()
    try:
        if ext in {"txt", "csv"}:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file_handle:
                return file_handle.read()

        if ext == "docx":
            import docx

            document = docx.Document(filepath)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)

        if ext == "pdf":
            import pdfplumber

            with pdfplumber.open(filepath) as pdf:
                return "\n\n".join(page.extract_text() or "" for page in pdf.pages)
    except Exception:
        return None
    return None


def extract_text_from_image(filepath: str) -> Optional[str]:
    """Extract text from an uploaded image using OCR if available."""
    try:
        from PIL import Image
        import pytesseract

        image = Image.open(filepath)
        return pytesseract.image_to_string(image)
    except Exception:
        return None


def make_unique_filename(filename: str) -> str:
    """Create a unique filename to avoid collisions in uploads."""
    return f"{uuid.uuid4().hex}_{secure_filename(filename)}"
