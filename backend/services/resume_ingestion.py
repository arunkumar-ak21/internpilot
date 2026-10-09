"""Resume storage, extraction, and conservative derived profile generation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
import asyncio

from docx import Document
from PyPDF2 import PdfReader

from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from backend.core.config import get_settings, UPLOADS_DIR

SUPPORTED_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

def get_llm():
    settings = get_settings()
    if settings.llm_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model_name=settings.llm_model, temperature=0.0, groq_api_key=settings.groq_api_key, max_retries=1, timeout=10.0)
    elif settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.llm_model, temperature=0.0, google_api_key=settings.gemini_api_key, max_retries=1, timeout=10.0)
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.llm_model, base_url=settings.llm_base_url, temperature=0.0, num_predict=512)

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

class Project(BaseModel):
    name: str = Field(description="Project name")
    technologies: list[str] = Field(description="Technologies used in this project")

class ResumeExtraction(BaseModel):
    skills: list[str] = Field(description="A list of technical and soft skills extracted from the resume with evidence.")
    email: str | None = Field(description="The email address of the candidate, if found.")
    education: list[str] = Field(default_factory=list, description="List of degrees or educational institutions found.")
    projects: list[Project] = Field(default_factory=list, description="Projects and their technologies")
    experience: list[str] = Field(default_factory=list, description="Work or internship experience")
    certifications: list[str] = Field(default_factory=list, description="Certifications")

async def parse_profile(text: str) -> dict:
    """Extract explicit facts from the resume using LangChain."""
    parser = PydanticOutputParser(pydantic_object=ResumeExtraction)
    llm = get_llm()
    settings = get_settings()
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR recruiter AI. Extract the exact skills, email, projects, experience, and education from the resume text provided. Do not invent any information. If something is missing, leave it empty or null.\n\n{format_instructions}"),
        ("user", "Resume Text:\n{text}")
    ])
    
    chain = prompt | llm | parser
    
    # Bounded chunk extraction
    max_chunk_len = 10000
    chunks = []
    if len(text) > max_chunk_len * 2:
        # Use first 10k and last 10k chars for very long resumes
        chunks = [text[:max_chunk_len], text[-max_chunk_len:]]
    elif len(text) > max_chunk_len:
        chunks = [text[:max_chunk_len], text[max_chunk_len:]]
    else:
        chunks = [text]

    extracted_results = []
    warnings = []
    
    for i, chunk in enumerate(chunks):
        try:
            res = await asyncio.wait_for(
                chain.ainvoke({"text": chunk, "format_instructions": parser.get_format_instructions()}),
                timeout=settings.llm_timeout
            )
            extracted_results.append(res)
        except asyncio.TimeoutError:
            warnings.append(f"Timeout processing chunk {i+1}")
        except Exception as e:
            warnings.append(f"LLM Parsing failed for chunk {i+1}: {e}")
            
    if not extracted_results:
        # Fallback to basic extraction
        import re
        lower = text.lower()
        skills = [s for s in ["python", "sql", "javascript", "react", "machine learning"] if s in lower]
        email = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
        return {
            "extraction_status": "partial",
            "extraction_method": "fallback-regex",
            "extraction_warnings": warnings + ["Fell back to regex extraction due to complete LLM failure."],
            "parsed_profile": {
                "skills": skills,
                "email": email.group(0) if email else None,
                "education": [],
                "projects": [],
                "experience": [],
                "certifications": []
            }
        }
        
    # Merge results
    merged_skills = set()
    merged_education = set()
    merged_experience = set()
    merged_certifications = set()
    merged_projects = []
    merged_email = None
    
    for r in extracted_results:
        merged_skills.update(r.skills)
        merged_education.update(r.education)
        merged_experience.update(r.experience)
        merged_certifications.update(r.certifications)
        merged_projects.extend(r.projects)
        if not merged_email and r.email:
            merged_email = r.email
            
    return {
        "extraction_status": "completed" if not warnings else "partial",
        "extraction_method": "langchain-llm",
        "extraction_warnings": warnings,
        "parsed_profile": {
            "skills": list(merged_skills),
            "email": merged_email,
            "education": list(merged_education),
            "projects": [p.model_dump() for p in merged_projects],
            "experience": list(merged_experience),
            "certifications": list(merged_certifications)
        }
    }


def store_original(file_name: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    original_name = sanitize_filename(file_name)
    stored = UPLOADS_DIR / f"{uuid.uuid4()}-{original_name}"
    stored.write_bytes(content)
    return stored


async def resume_payload(student_id: str, file_name: str, content: bytes, content_type: str) -> dict:
    expected_suffix = SUPPORTED_TYPES.get(content_type)
    if not expected_suffix or Path(file_name).suffix.lower() != expected_suffix:
        raise ValueError("File extension and content type must be a supported matching pair")
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("Resume must be between 1 byte and 10 MB")
    extracted = extract_text(content, content_type)
    path = store_original(file_name, content)
    parsed_result = await parse_profile(extracted)
    return {
        "resume_id": str(uuid.uuid4()), 
        "student_id": student_id, 
        "file_name": sanitize_filename(file_name), 
        "file_path": str(path), 
        "version": 1, 
        "extracted_text": extracted, 
        "parsed_profile": parsed_result["parsed_profile"], 
        "extraction_metadata": {
            "status": parsed_result["extraction_status"],
            "method": parsed_result["extraction_method"],
            "warnings": parsed_result["extraction_warnings"]
        },
        "created_at": datetime.now(UTC).isoformat()
    }
