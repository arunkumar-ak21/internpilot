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
import json
from pathlib import Path
from io import BytesIO
from docx import Document
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.core.config import get_settings

def get_llm():
    settings = get_settings()
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model_name=settings.llm_model, temperature=0.0, groq_api_key=settings.groq_api_key, max_retries=1, timeout=10.0)
    elif settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.llm_model, temperature=0.0, google_api_key=settings.gemini_api_key)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.llm_model, base_url=settings.llm_base_url, temperature=0.0)

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

class ResumeExtraction(BaseModel):
    skills: list[str] = Field(description="A list of technical and soft skills extracted from the resume.")
    email: str | None = Field(description="The email address of the candidate, if found.")
    education: list[str] = Field(description="List of degrees or educational institutions found.")

def parse_profile(text: str) -> dict:
    """Extract explicit facts from the resume using LangChain."""
    parser = PydanticOutputParser(pydantic_object=ResumeExtraction)
    llm = get_llm()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR recruiter AI. Extract the exact skills, email, and education from the resume text provided. Do not invent any information. If something is missing, leave it empty or null.\n\n{format_instructions}"),
        ("user", "Resume Text:\n{text}")
    ])
    
    chain = prompt | llm | parser
    
    try:
        # We run it synchronously since this is called in a standard function for now, 
        # or we could make parse_profile async. Assuming standard function for this flow.
        # However, to avoid blocking, normally this would be async.
        extracted = chain.invoke({"text": text, "format_instructions": parser.get_format_instructions()})
        return {
            "skills": extracted.skills,
            "email": extracted.email,
            "education": extracted.education,
            "parser": "langchain-ollama"
        }
    except Exception as e:
        print(f"LLM Parsing failed: {e}")
        # Fallback to basic extraction
        import re
        lower = text.lower()
        skills = [s for s in ["python", "sql", "javascript", "react", "machine learning"] if s in lower]
        email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
        return {"skills": skills, "email": email.group(0) if email else None, "parser": "fallback-regex"}


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
