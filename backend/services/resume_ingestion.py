"""
Resume Ingestion & LLM Profile Intelligence Engine

Uses Groq / OpenRouter LLM to semantically read resumes, understand candidate
projects and experience, extract skills without dictionary limits, and infer
tailored role tracks. Keeps a deterministic fallback for offline unit tests.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
from dotenv import dotenv_values

from backend.core.config import get_settings, UPLOADS_DIR

ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

SUPPORTED_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

# ==========================================================
# Shared Direct LLM Engine (Groq & OpenRouter via httpx)
# ==========================================================

async def call_llm_direct(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1200,
    temperature: float = 0.2,
    json_mode: bool = False,
) -> tuple[str | None, str]:
    """
    Call Groq or OpenRouter directly via httpx.AsyncClient.
    Reads .env fresh on every call so cached settings never block API keys.
    Returns (response_text, model_label).
    """
    env_vars = dotenv_values(ENV_PATH) if ENV_PATH.exists() else {}
    openrouter_key = (env_vars.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY") or "").strip()
    groq_key = (env_vars.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY") or "").strip()
    provider_pref = (env_vars.get("LLM_PROVIDER") or os.environ.get("LLM_PROVIDER") or "groq").lower().strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 1. OpenRouter (if preferred or if only OpenRouter key is provided)
    if openrouter_key and (provider_pref == "openrouter" or not groq_key):
        or_model = (env_vars.get("OPENROUTER_MODEL") or "meta-llama/llama-3.3-70b-instruct").strip()
        payload: dict[str, Any] = {
            "model": or_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"},
                    json=payload,
                    timeout=20.0,
                )
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    return content, f"OpenRouter ({or_model})"
        except Exception as e:
            print(f"[OpenRouter Error] {e}")

    # 2. Groq (automatic fallback from 70B to 8B-instant if rate-limited)
    if groq_key:
        for model_name in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                payload["response_format"] = {"type": "json_object"}
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                        json=payload,
                        timeout=18.0,
                    )
                    if resp.status_code == 200:
                        content = resp.json()["choices"][0]["message"]["content"].strip()
                        return content, f"Groq ({model_name})"
                    else:
                        print(f"[Groq HTTP {resp.status_code} on {model_name}] {resp.text[:180]}")
            except Exception as e:
                print(f"[Groq Error on {model_name}] {e}")

    return None, "OfflineFallback"


def _extract_json_object(raw_text: str) -> dict | None:
    """Safely parse JSON from an LLM response even if wrapped in markdown code fences."""
    if not raw_text:
        return None
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
    return None


async def call_llm_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1400,
    temperature: float = 0.1,
) -> tuple[dict | None, str]:
    """Call the LLM and parse the returned JSON object."""
    text, source = await call_llm_direct(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=True,
    )
    if text:
        parsed = _extract_json_object(text)
        if isinstance(parsed, dict):
            return parsed, source

    # Retry once without strict json_mode in case the model prefers raw markdown JSON
    text2, source2 = await call_llm_direct(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        json_mode=False,
    )
    if text2:
        parsed2 = _extract_json_object(text2)
        if isinstance(parsed2, dict):
            return parsed2, source2

    return None, source


def get_llm():
    """Backward-compatible LangChain LLM getter for legacy skills."""
    settings = get_settings()
    if settings.groq_api_key:
        from langchain_groq import ChatGroq
        model_name = settings.llm_model
        if ":" in model_name or "llama3-70b-8192" in model_name:
            model_name = "llama-3.3-70b-versatile"
        return ChatGroq(
            model_name=model_name,
            temperature=0.1,
            groq_api_key=settings.groq_api_key,
            max_retries=1,
            timeout=15.0,
        )
    from langchain_ollama import ChatOllama
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        temperature=0.1,
        num_predict=512,
    )


# ==========================================================
# File Sanitization & Raw Text Extraction
# ==========================================================

def sanitize_filename(name: str) -> str:
    clean = Path(name).name
    if not clean or clean in {".", ".."}:
        raise ValueError("A valid file name is required")
    return clean


def extract_text(content: bytes, content_type: str) -> str:
    """Extract raw text from supported file types (.txt, .pdf, .docx)."""
    base_type = (content_type or "").split(";")[0].strip().lower()
    if base_type == "text/plain":
        return content.decode("utf-8", errors="replace")
    if base_type == "application/pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            from PyPDF2 import PdfReader
        reader = PdfReader(BytesIO(content))
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        full_text = "\n".join(pages_text)
        if not full_text.strip():
            try:
                import pdfplumber
                with pdfplumber.open(BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            pages_text.append(text)
                full_text = "\n".join(pages_text)
            except ImportError:
                pass
        return full_text
    if base_type.endswith("wordprocessingml.document"):
        from docx import Document
        return "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs)
    raise ValueError("Unsupported resume format")


# ==========================================================
# LLM-Driven Semantic Resume Understanding (Stage 1 Brain)
# ==========================================================

async def parse_profile_with_llm(text: str, file_name: str | None = None) -> dict:
    """
    Use the LLM Brain (Groq / OpenRouter) to semantically read the candidate's resume,
    rank their skills by real project/work depth, extract their projects, and infer
    personalized internship role tracks.
    """
    sys_prompt = (
        "You are an expert Technical Recruiter and Resume Intelligence Agent.\n"
        "Read the candidate's raw resume text carefully and extract a structured JSON profile.\n"
        "CRITICAL RULES:\n"
        "1. Do NOT list skills alphabetically. Order `skills_display` from #1 most important/specialized "
        "skill (proven in their projects and internships) down to minor tools.\n"
        "2. Infer 4 to 6 `inferred_roles` that specifically match THIS candidate's unique project stack and strengths.\n"
        "3. Generate 5 short `search_queries` (2-3 words each, ending in 'intern') tailored to their exact specialization.\n"
        "4. Return ONLY valid JSON matching the exact schema requested."
    )

    user_prompt = (
        f"Resume Filename: {file_name or 'resume.pdf'}\n"
        f"Raw Resume Text:\n\"\"\"\n{text[:6000]}\n\"\"\"\n\n"
        "Return a JSON object with these exact keys:\n"
        "{\n"
        '  "name": "Candidate Full Name",\n'
        '  "email": "email or null",\n'
        '  "phone": "phone or null",\n'
        '  "cgpa": 8.5, // float on 10-point scale or null\n'
        '  "skills_display": ["TopSkill1", "TopSkill2", ...], // ordered by depth of use in projects/work\n'
        '  "project_skills": ["SkillUsedInProjects1", "SkillUsedInProjects2", ...],\n'
        '  "inferred_roles": ["Specific Role Intern 1", "Specific Role Intern 2", ...],\n'
        '  "search_queries": ["specific skill intern", "domain role intern", ...],\n'
        '  "education": [{"degree": "Degree & Branch", "institution": "College Name", "cgpa": 8.5, "graduation_year": 2027}],\n'
        '  "projects": [{"name": "Project Title", "description": "1-sentence summary of what was built and impact", "technologies": ["Tech1", "Tech2"]}],\n'
        '  "experience": ["Role at Company — key achievement"],\n'
        '  "core_strengths": "2-sentence recruiter analysis of what makes this candidate unique",\n'
        '  "summary": "Concise 2-sentence candidate summary"\n'
        "}"
    )

    llm_data, llm_source = await call_llm_json(sys_prompt, user_prompt, max_tokens=1400, temperature=0.1)

    if llm_data and isinstance(llm_data.get("skills_display"), list) and len(llm_data["skills_display"]) > 0:
        skills_display = [str(s).strip() for s in llm_data["skills_display"] if str(s).strip()]
        cgpa_val = llm_data.get("cgpa")
        try:
            cgpa_val = float(cgpa_val) if cgpa_val is not None else extract_cgpa(text)
        except Exception:
            cgpa_val = extract_cgpa(text)

        return {
            "name": llm_data.get("name") or extract_name(text, file_name) or "Candidate",
            "email": llm_data.get("email") or extract_email(text),
            "phone": llm_data.get("phone") or extract_phone(text),
            "skills": [s.lower() for s in skills_display],
            "skills_display": skills_display,
            "project_skills": llm_data.get("project_skills") or skills_display[:8],
            "inferred_roles": llm_data.get("inferred_roles") or ["Software Engineering Intern"],
            "search_queries": llm_data.get("search_queries") or [],
            "education": llm_data.get("education") or extract_education(text),
            "cgpa": cgpa_val,
            "projects": llm_data.get("projects") or [],
            "experience": llm_data.get("experience") or [],
            "certifications": [],
            "core_strengths": llm_data.get("core_strengths") or "",
            "summary": llm_data.get("summary") or f"Parsed via {llm_source}.",
            "llm_source": llm_source,
        }

    # Fallback if offline or in unit tests without API key
    fallback = parse_profile_deterministic(text, file_name=file_name)
    fallback["llm_source"] = "DeterministicFallback"
    return fallback


# ==========================================================
# Offline Fallback Helpers (For Unit Tests & Offline Mode)
# ==========================================================

SKILL_DICTIONARY = {
    "python": "Python", "java": "Java", "javascript": "JavaScript",
    "typescript": "TypeScript", "c++": "C++", "c": "C", "c#": "C#",
    "go": "Go", "rust": "Rust", "sql": "SQL", "kotlin": "Kotlin",
    "swift": "Swift", "dart": "Dart", "bash": "Bash", "html": "HTML", "css": "CSS",
    "machine learning": "Machine Learning", "deep learning": "Deep Learning",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "scikit-learn": "Scikit-Learn",
    "opencv": "OpenCV", "yolov11": "YOLOv11", "yolo": "YOLO",
    "computer vision": "Computer Vision", "nlp": "NLP",
    "reinforcement learning": "Reinforcement Learning", "q-learning": "Q-Learning",
    "langchain": "LangChain", "langgraph": "LangGraph", "rag": "RAG",
    "chromadb": "ChromaDB", "ollama": "Ollama", "generative ai": "Generative AI",
    "pandas": "Pandas", "numpy": "NumPy", "data science": "Data Science",
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "node.js": "Node.js", "nodejs": "Node.js", "express.js": "Express.js",
    "spring boot": "Spring Boot", "react": "React", "next.js": "Next.js",
    "postgresql": "PostgreSQL", "mysql": "MySQL", "mongodb": "MongoDB",
    "redis": "Redis", "sqlite": "SQLite", "supabase": "Supabase", "firebase": "Firebase",
    "rest api": "REST API", "graphql": "GraphQL", "websockets": "WebSockets",
    "webrtc": "WebRTC", "docker": "Docker", "kubernetes": "Kubernetes",
    "aws": "AWS", "gcp": "Google Cloud Platform", "oci": "Oracle Cloud Infrastructure",
    "linux": "Linux", "git": "Git", "github": "GitHub", "ci/cd": "CI/CD",
    "flutter": "Flutter", "react native": "React Native", "android": "Android Development",
    "iot": "IoT", "esp32": "ESP32", "embedded systems": "Embedded Systems",
}

SPECIALIZED_SKILLS = {
    "Flutter", "React Native", "Android Development", "React", "Next.js",
    "Node.js", "Express.js", "FastAPI", "Django", "Flask", "Spring Boot",
    "MongoDB", "PostgreSQL", "Redis", "Supabase", "Firebase",
    "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
    "Computer Vision", "OpenCV", "YOLO", "YOLOv11", "NLP",
    "Reinforcement Learning", "Q-Learning", "RAG", "LangChain", "LangGraph",
    "Generative AI", "Ollama", "ChromaDB", "Docker", "Kubernetes", "AWS",
    "Oracle Cloud Infrastructure", "WebSockets", "WebRTC", "IoT", "ESP32",
}

GENERIC_BASELINE_SKILLS = {"C", "HTML", "CSS", "Git", "GitHub"}


def extract_skills_deterministic(text: str) -> list[str]:
    lower_text = text.lower()
    for ch in [",", "|", "•", "●", "▪", "/", "(", ")", "[", "]", ":", ";"]:
        lower_text = lower_text.replace(ch, " ")

    counts: dict[str, int] = {}
    for key in sorted(SKILL_DICTIONARY.keys(), key=len, reverse=True):
        canonical = SKILL_DICTIONARY[key]
        if len(key) <= 3:
            matches = re.findall(r"(?<![a-zA-Z0-9])" + re.escape(key) + r"(?![a-zA-Z0-9+#])", lower_text)
            if matches:
                counts[canonical] = counts.get(canonical, 0) + len(matches)
        else:
            c = lower_text.count(key)
            if c > 0:
                counts[canonical] = counts.get(canonical, 0) + c

    return sorted(
        counts.keys(),
        key=lambda s: (-(min(counts[s], 5) + (3.0 if s in SPECIALIZED_SKILLS else 1.0)), s),
    )


def extract_email(text: str) -> str | None:
    m = re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", text)
    return m.group(0) if m else None


def extract_phone(text: str) -> str | None:
    m = re.search(r"(?:\+?\d{1,3}[\s\-]?)?[6-9]\d{9}|\+?\d[\d\s\-\(\)]{9,14}\d", text)
    return m.group(0).strip() if m else None


def extract_name(text: str, file_name: str | None = None) -> str | None:
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]
    skip = {"resume", "curriculum", "vitae", "summary", "profile", "education", "skills", "projects"}
    for line in lines[:6]:
        part = re.split(r"[|•●]|https?://|[\w.+-]+@", line)[0].strip()
        words = part.split()
        if 1 <= len(words) <= 5 and not any(w.lower() in skip for w in words):
            if all(w.replace(".", "").replace("-", "").isalpha() for w in words):
                return part.title() if part.isupper() else part
    return None


def extract_cgpa(text: str) -> float | None:
    m = re.search(r"(?:CGPA|GPA|CPI)\s*[:\-]?\s*(\d+\.?\d*)", text, re.I)
    if m and 0 < float(m.group(1)) <= 10:
        return float(m.group(1))
    return None


def extract_education(text: str) -> list[dict]:
    cgpa = extract_cgpa(text)
    return [{"degree": "Bachelor of Engineering", "cgpa": cgpa}] if cgpa else []


def parse_profile_deterministic(text: str, file_name: str | None = None) -> dict:
    skills = extract_skills_deterministic(text)
    name = extract_name(text, file_name=file_name) or "Candidate"
    cgpa = extract_cgpa(text)
    inferred = ["Software Engineering Intern"]
    if any(s in skills for s in ["Machine Learning", "Deep Learning", "OpenCV", "RAG"]):
        inferred.insert(0, "AI & Machine Learning Intern")
    if any(s in skills for s in ["React", "Node.js", "FastAPI", "Django", "Flutter"]):
        inferred.insert(0, "Full Stack / Backend Developer Intern")
    return {
        "name": name,
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": [s.lower() for s in skills],
        "skills_display": skills,
        "project_skills": skills[:8],
        "inferred_roles": inferred,
        "education": extract_education(text),
        "cgpa": cgpa,
        "projects": [],
        "experience": [],
        "certifications": [],
        "summary": f"{name} with {len(skills)} extracted skills.",
    }


class ProfileResult(dict):
    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()


def parse_profile(text: str, file_name: str | None = None) -> ProfileResult:
    """Synchronous entry point kept for unit test compatibility."""
    profile = parse_profile_deterministic(text, file_name=file_name)
    return ProfileResult({
        **profile,
        "extraction_status": "completed",
        "extraction_method": "deterministic",
        "extraction_warnings": [],
        "parsed_profile": profile,
    })


def store_original(file_name: str, content: bytes) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    original_name = sanitize_filename(file_name)
    stored = UPLOADS_DIR / f"{uuid.uuid4()}-{original_name}"
    stored.write_bytes(content)
    return stored


def resume_payload(student_id: str, file_name: str, content: bytes, content_type: str):
    clean_type = (content_type or "").split(";")[0].strip().lower()
    suffix = Path(file_name).suffix.lower()

    if clean_type == "application/octet-stream":
        ext_to_mime = {v: k for k, v in SUPPORTED_TYPES.items()}
        if suffix in ext_to_mime:
            clean_type = ext_to_mime[suffix]

    expected_suffix = SUPPORTED_TYPES.get(clean_type)
    if not expected_suffix or suffix != expected_suffix:
        raise ValueError("File extension and content type must be a supported matching pair")
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("Resume must be between 1 byte and 10 MB")

    async def _build():
        extracted = extract_text(content, clean_type)
        path = store_original(file_name, content)
        # Use the LLM Brain to semantically read and analyze the resume!
        parsed_inner = await parse_profile_with_llm(extracted, file_name=file_name)
        rid = str(uuid.uuid4())
        parsed_inner["resume_id"] = rid
        parsed_inner["student_id"] = student_id
        parsed_inner["file_name"] = sanitize_filename(file_name)
        return {
            "resume_id": rid,
            "student_id": student_id,
            "file_name": sanitize_filename(file_name),
            "file_path": str(path),
            "version": 1,
            "extracted_text": extracted,
            "parsed_profile": parsed_inner,
            "extraction_metadata": {
                "status": "completed",
                "method": parsed_inner.get("llm_source", "llm"),
                "warnings": [],
            },
            "created_at": datetime.now(UTC).isoformat(),
        }

    return _build()