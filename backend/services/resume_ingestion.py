"""Resume storage, extraction, and conservative derived profile generation."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from docx import Document
from PyPDF2 import PdfReader

from backend.core.config import UPLOADS_DIR

SUPPORTED_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
KNOWN_SKILLS = {"python", "sql", "pytorch", "tensorflow", "fastapi", "react", "javascript", "machine learning"}


def sanitize_filename(name: str) -> str:
    clean = Path(name).name
    if not clean or clean in {".", ".."}:
        raise ValueError("A valid file name is required")
    return clean


def extract_text(content: bytes, content_type: str) -> str:
    if content_type == "text/plain":
        return content.decode("utf-8")
    if content_type == "application/pdf":
        return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    if content_type.endswith("wordprocessingml.document"):
        return "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs)
    raise ValueError("Unsupported resume format")


def parse_profile(text: str) -> dict:
    """Extract only explicit facts; unknown facts remain absent rather than inferred."""
    lower = text.lower()
    skills = sorted(skill for skill in KNOWN_SKILLS if skill in lower)
    email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return {"skills": skills, "email": email.group(0) if email else None, "parser": "deterministic-keyword-v1"}


def store_original(file_name: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    original_name = sanitize_filename(file_name)
    stored = UPLOADS_DIR / f"{uuid.uuid4()}-{original_name}"
    stored.write_bytes(content)
    return stored


def resume_payload(student_id: str, file_name: str, content: bytes, content_type: str) -> dict:
    expected_suffix = SUPPORTED_TYPES.get(content_type)
    if not expected_suffix or Path(file_name).suffix.lower() != expected_suffix:
        raise ValueError("File extension and content type must be a supported matching pair")
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("Resume must be between 1 byte and 10 MB")
    extracted = extract_text(content, content_type)
    path = store_original(file_name, content)
    return {"resume_id": str(uuid.uuid4()), "student_id": student_id, "file_name": sanitize_filename(file_name), "file_path": str(path), "version": 1, "extracted_text": extracted, "parsed_profile": parse_profile(extracted), "created_at": datetime.now(UTC).isoformat()}
