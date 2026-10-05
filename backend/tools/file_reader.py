"""Restricted file-reading tool for uploaded text resumes."""

from backend.core.config import UPLOADS_DIR


def read_uploaded_text(file_name: str) -> dict[str, str]:
    """Read a `.txt` upload only; prevent path traversal and arbitrary reads."""
    path = (UPLOADS_DIR / file_name).resolve()
    if path.parent != UPLOADS_DIR.resolve():
        raise ValueError("File must be inside the upload directory")
    if path.suffix.lower() != ".txt":
        raise ValueError("Only .txt files are supported by the Lab 2 reader")
    if not path.is_file():
        raise FileNotFoundError("Uploaded file was not found")
    return {"file_name": path.name, "text": path.read_text(encoding="utf-8")}
