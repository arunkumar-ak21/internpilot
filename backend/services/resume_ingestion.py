"""Resume storage, extraction, and comprehensive profile generation."""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
import asyncio

from backend.core.config import get_settings, UPLOADS_DIR

SUPPORTED_TYPES = {
    "text/plain": ".txt",
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}

# =============================================
# Comprehensive Skill Dictionary (150+ skills)
# =============================================

SKILL_DICTIONARY = {
    # Programming Languages
    "python": "Python", "java": "Java", "javascript": "JavaScript",
    "typescript": "TypeScript", "c++": "C++", "c#": "C#", "go": "Go",
    "golang": "Go", "rust": "Rust", "ruby": "Ruby", "php": "PHP",
    "swift": "Swift", "kotlin": "Kotlin", "scala": "Scala", "r": "R",
    "matlab": "MATLAB", "perl": "Perl", "dart": "Dart", "lua": "Lua",
    "shell": "Shell Scripting", "bash": "Bash", "powershell": "PowerShell",
    "sql": "SQL", "html": "HTML", "css": "CSS", "sass": "SASS",
    "less": "LESS",

    # AI/ML & Data Science
    "machine learning": "Machine Learning", "deep learning": "Deep Learning",
    "neural network": "Neural Networks", "natural language processing": "NLP",
    "nlp": "NLP", "computer vision": "Computer Vision",
    "reinforcement learning": "Reinforcement Learning",
    "pytorch": "PyTorch", "tensorflow": "TensorFlow", "keras": "Keras",
    "scikit-learn": "Scikit-Learn", "sklearn": "Scikit-Learn",
    "opencv": "OpenCV", "yolo": "YOLO", "hugging face": "Hugging Face",
    "huggingface": "Hugging Face", "transformers": "Transformers",
    "langchain": "LangChain", "langgraph": "LangGraph",
    "llamaindex": "LlamaIndex", "llama index": "LlamaIndex",
    "rag": "RAG", "retrieval augmented generation": "RAG",
    "chromadb": "ChromaDB", "chroma": "ChromaDB",
    "pinecone": "Pinecone", "weaviate": "Weaviate", "faiss": "FAISS",
    "ollama": "Ollama", "openai": "OpenAI API", "gemini": "Google Gemini",
    "gpt": "GPT Models", "llm": "Large Language Models",
    "generative ai": "Generative AI", "genai": "Generative AI",
    "stable diffusion": "Stable Diffusion", "diffusion model": "Diffusion Models",
    "pandas": "Pandas", "numpy": "NumPy", "scipy": "SciPy",
    "matplotlib": "Matplotlib", "seaborn": "Seaborn", "plotly": "Plotly",
    "tableau": "Tableau", "power bi": "Power BI",
    "data analysis": "Data Analysis", "data science": "Data Science",
    "data engineering": "Data Engineering", "etl": "ETL",
    "apache spark": "Apache Spark", "spark": "Apache Spark",
    "hadoop": "Hadoop", "kafka": "Apache Kafka", "airflow": "Apache Airflow",
    "mlops": "MLOps", "mlflow": "MLflow",
    "feature engineering": "Feature Engineering",
    "model deployment": "Model Deployment",
    "statistical analysis": "Statistical Analysis",
    "time series": "Time Series Analysis",
    "recommendation system": "Recommendation Systems",
    "image classification": "Image Classification",
    "object detection": "Object Detection",
    "semantic segmentation": "Semantic Segmentation",
    "speech recognition": "Speech Recognition",
    "text classification": "Text Classification",
    "sentiment analysis": "Sentiment Analysis",

    # Backend & Web Frameworks
    "fastapi": "FastAPI", "flask": "Flask", "django": "Django",
    "express": "Express.js", "express.js": "Express.js",
    "node.js": "Node.js", "nodejs": "Node.js", "node": "Node.js",
    "spring": "Spring", "spring boot": "Spring Boot",
    "asp.net": "ASP.NET", ".net": ".NET",
    "ruby on rails": "Ruby on Rails", "rails": "Ruby on Rails",
    "gin": "Gin (Go)", "fiber": "Fiber (Go)",
    "next.js": "Next.js", "nextjs": "Next.js",
    "nuxt": "Nuxt.js", "nuxt.js": "Nuxt.js",
    "nest.js": "NestJS", "nestjs": "NestJS",

    # Frontend Frameworks & Libraries
    "react": "React", "reactjs": "React", "react.js": "React",
    "angular": "Angular", "vue": "Vue.js", "vue.js": "Vue.js",
    "svelte": "Svelte", "jquery": "jQuery",
    "tailwind": "Tailwind CSS", "tailwindcss": "Tailwind CSS",
    "bootstrap": "Bootstrap", "material ui": "Material UI",
    "chakra ui": "Chakra UI", "shadcn": "shadcn/ui",
    "redux": "Redux", "zustand": "Zustand",
    "framer motion": "Framer Motion",
    "three.js": "Three.js", "threejs": "Three.js",
    "webpack": "Webpack", "vite": "Vite",
    "responsive design": "Responsive Design",

    # Databases
    "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "mysql": "MySQL", "mongodb": "MongoDB", "redis": "Redis",
    "sqlite": "SQLite", "oracle": "Oracle DB",
    "cassandra": "Cassandra", "dynamodb": "DynamoDB",
    "elasticsearch": "Elasticsearch", "neo4j": "Neo4j",
    "supabase": "Supabase", "firebase": "Firebase",
    "firestore": "Firestore", "couchdb": "CouchDB",
    "cockroachdb": "CockroachDB",

    # DevOps, Cloud & Infrastructure
    "docker": "Docker", "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "ansible": "Ansible",
    "jenkins": "Jenkins", "github actions": "GitHub Actions",
    "gitlab ci": "GitLab CI/CD", "ci/cd": "CI/CD",
    "aws": "AWS", "amazon web services": "AWS",
    "gcp": "Google Cloud Platform", "google cloud": "Google Cloud Platform",
    "azure": "Microsoft Azure",
    "heroku": "Heroku", "vercel": "Vercel", "netlify": "Netlify",
    "digitalocean": "DigitalOcean",
    "nginx": "Nginx", "apache": "Apache HTTP",
    "linux": "Linux", "ubuntu": "Ubuntu",
    "git": "Git", "github": "GitHub", "gitlab": "GitLab",
    "prometheus": "Prometheus", "grafana": "Grafana",
    "cloudflare": "Cloudflare",
    "serverless": "Serverless Architecture",
    "lambda": "AWS Lambda", "s3": "AWS S3", "ec2": "AWS EC2",
    "oci": "Oracle Cloud Infrastructure",
    "cloud functions": "Google Cloud Functions",

    # APIs & Communication
    "rest api": "REST API", "rest": "REST API",
    "graphql": "GraphQL", "grpc": "gRPC",
    "websocket": "WebSockets", "websockets": "WebSockets",
    "mqtt": "MQTT", "rabbitmq": "RabbitMQ",
    "microservices": "Microservices",
    "api gateway": "API Gateway",
    "oauth": "OAuth", "jwt": "JWT Authentication",
    "postman": "Postman",

    # Testing
    "pytest": "Pytest", "jest": "Jest", "mocha": "Mocha",
    "cypress": "Cypress", "selenium": "Selenium",
    "unittest": "Unit Testing", "unit testing": "Unit Testing",
    "integration testing": "Integration Testing",
    "test driven development": "TDD", "tdd": "TDD",

    # Mobile
    "react native": "React Native", "flutter": "Flutter",
    "android": "Android Development", "ios": "iOS Development",
    "swiftui": "SwiftUI",

    # Other
    "agile": "Agile Methodology", "scrum": "Scrum",
    "jira": "Jira", "confluence": "Confluence",
    "figma": "Figma", "canva": "Canva",
    "latex": "LaTeX", "markdown": "Markdown",
    "blockchain": "Blockchain", "web3": "Web3",
    "embedded systems": "Embedded Systems",
    "iot": "IoT", "internet of things": "IoT",
    "robotics": "Robotics", "ros": "ROS",
    "arduino": "Arduino", "raspberry pi": "Raspberry Pi",
}

# Role inference rules: (required_skills_set, inferred_roles)
ROLE_INFERENCE_RULES = [
    ({"Machine Learning", "Deep Learning"}, ["AI/ML Engineering Intern", "Data Science Intern"]),
    ({"PyTorch"}, ["AI/ML Engineering Intern"]),
    ({"TensorFlow"}, ["AI/ML Engineering Intern"]),
    ({"Computer Vision", "OpenCV"}, ["Computer Vision Intern", "AI/ML Engineering Intern"]),
    ({"NLP"}, ["NLP Engineering Intern", "AI/ML Engineering Intern"]),
    ({"LangChain"}, ["GenAI / LLM Engineering Intern"]),
    ({"LangGraph"}, ["GenAI / LLM Engineering Intern"]),
    ({"RAG"}, ["GenAI / LLM Engineering Intern"]),
    ({"Large Language Models"}, ["GenAI / LLM Engineering Intern"]),
    ({"Generative AI"}, ["GenAI / LLM Engineering Intern"]),
    ({"FastAPI"}, ["Backend Engineering Intern", "Python Developer Intern"]),
    ({"Django"}, ["Backend Engineering Intern", "Python Developer Intern"]),
    ({"Flask"}, ["Backend Engineering Intern", "Python Developer Intern"]),
    ({"React", "Node.js"}, ["Full-Stack Developer Intern"]),
    ({"React"}, ["Frontend Developer Intern"]),
    ({"Vue.js"}, ["Frontend Developer Intern"]),
    ({"Angular"}, ["Frontend Developer Intern"]),
    ({"Next.js"}, ["Full-Stack Developer Intern"]),
    ({"Docker", "Kubernetes"}, ["DevOps / Cloud Engineering Intern"]),
    ({"AWS"}, ["Cloud Engineering Intern"]),
    ({"Google Cloud Platform"}, ["Cloud Engineering Intern"]),
    ({"Terraform"}, ["DevOps / Cloud Engineering Intern"]),
    ({"CI/CD"}, ["DevOps Engineering Intern"]),
    ({"Apache Spark"}, ["Data Engineering Intern"]),
    ({"Data Engineering"}, ["Data Engineering Intern"]),
    ({"Data Science"}, ["Data Science Intern"]),
    ({"Pandas", "NumPy"}, ["Data Science Intern", "Data Analysis Intern"]),
    ({"PostgreSQL"}, ["Backend Engineering Intern"]),
    ({"MongoDB"}, ["Backend Engineering Intern"]),
    ({"Spring Boot"}, ["Java Backend Intern"]),
    ({"Flutter"}, ["Mobile Development Intern"]),
    ({"React Native"}, ["Mobile Development Intern"]),
    ({"Android Development"}, ["Android Developer Intern"]),
    ({"Embedded Systems"}, ["Embedded Systems Intern"]),
    ({"IoT"}, ["IoT Engineering Intern"]),
    ({"Blockchain"}, ["Blockchain Developer Intern"]),
    ({"Python"}, ["Software Engineering Intern"]),
    ({"Java"}, ["Software Engineering Intern"]),
    ({"JavaScript"}, ["Software Engineering Intern"]),
]


def get_llm():
    """Get the configured LLM instance."""
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
    """Extract raw text from supported file types."""
    if content_type == "text/plain":
        return content.decode("utf-8", errors="replace")
    if content_type == "application/pdf":
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
            # Try pdfplumber as fallback for scanned PDFs
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
    if content_type.endswith("wordprocessingml.document"):
        from docx import Document
        return "\n".join(paragraph.text for paragraph in Document(BytesIO(content)).paragraphs)
    raise ValueError("Unsupported resume format")


def extract_skills_deterministic(text: str) -> list[str]:
    """Extract skills from resume text using comprehensive dictionary matching."""
    lower_text = text.lower()
    # Normalize common separators
    lower_text = lower_text.replace(",", " ").replace("|", " ").replace("•", " ").replace("●", " ")

    found_skills = set()

    # Sort by key length descending so multi-word matches take priority
    sorted_keys = sorted(SKILL_DICTIONARY.keys(), key=len, reverse=True)

    for key in sorted_keys:
        canonical = SKILL_DICTIONARY[key]
        if canonical in found_skills:
            continue

        # Use word boundary matching for short keys to reduce false positives
        if len(key) <= 3:
            # For very short keys (C++, R, Go, SQL, etc.) require word boundary
            pattern = r'(?<![a-zA-Z])' + re.escape(key) + r'(?![a-zA-Z+#])'
            if re.search(pattern, lower_text):
                found_skills.add(canonical)
        else:
            if key in lower_text:
                found_skills.add(canonical)

    return sorted(found_skills)


def extract_email(text: str) -> str | None:
    """Extract email address from text."""
    match = re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', text)
    return match.group(0) if match else None


def extract_phone(text: str) -> str | None:
    """Extract phone number from text."""
    match = re.search(r'[\+]?[\d\s\-\(\)]{10,15}', text)
    return match.group(0).strip() if match else None


def extract_name(text: str) -> str | None:
    """Extract candidate name (usually the first non-empty line)."""
    lines = text.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        # Skip lines that look like section headers or contain common resume keywords
        if not line or len(line) > 60:
            continue
        if any(kw in line.lower() for kw in ['resume', 'curriculum', 'objective', 'summary', 'profile', 'address', 'phone', 'email', '@', 'http']):
            continue
        # A name is typically 2-4 words, all alphabetic
        words = line.split()
        if 1 <= len(words) <= 5 and all(w.replace('.', '').replace('-', '').isalpha() for w in words):
            return line
    return None


def extract_education(text: str) -> list[dict]:
    """Extract education details including degree, institution, year, CGPA."""
    education_entries = []

    # Common degree patterns
    degree_patterns = [
        r'(?:B\.?Tech|B\.?E\.?|Bachelor(?:\s+of)?\s+(?:Technology|Engineering|Science|Arts|Commerce))',
        r'(?:M\.?Tech|M\.?E\.?|Master(?:\s+of)?\s+(?:Technology|Engineering|Science|Arts|Commerce|Business))',
        r'(?:M\.?S\.?|M\.?Sc\.?)',
        r'(?:B\.?Sc\.?|B\.?S\.?)',
        r'(?:B\.?C\.?A\.?|M\.?C\.?A\.?)',
        r'(?:MBA|Ph\.?D\.?)',
        r'(?:B\.?Com\.?|M\.?Com\.?)',
        r'(?:Diploma)',
    ]

    combined_degree = '|'.join(f'({p})' for p in degree_patterns)

    # Find lines containing degree keywords
    lines = text.split('\n')
    for i, line in enumerate(lines):
        for pattern in degree_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                entry = {"degree": line.strip()[:120]}

                # Look for CGPA/GPA in nearby lines
                context = "\n".join(lines[max(0, i-1):min(len(lines), i+3)])
                cgpa_match = re.search(r'(?:CGPA|GPA|CPI|SPI)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:/\s*(\d+\.?\d*))?', context, re.IGNORECASE)
                if cgpa_match:
                    entry["cgpa"] = float(cgpa_match.group(1))
                    if cgpa_match.group(2):
                        entry["scale"] = float(cgpa_match.group(2))

                # Look for percentage
                pct_match = re.search(r'(\d{2,3}(?:\.\d+)?)\s*%', context)
                if pct_match and not cgpa_match:
                    entry["percentage"] = float(pct_match.group(1))

                # Look for year
                year_match = re.search(r'(?:20\d{2})\s*[-–]\s*(20\d{2}|present|ongoing)', context, re.IGNORECASE)
                if year_match:
                    entry["year_range"] = year_match.group(0)
                else:
                    year_match = re.search(r'(20\d{2})', context)
                    if year_match:
                        entry["graduation_year"] = int(year_match.group(1))

                education_entries.append(entry)
                break

    return education_entries


def extract_cgpa(text: str) -> float | None:
    """Extract the primary CGPA/GPA from the resume."""
    match = re.search(r'(?:CGPA|GPA|CPI)\s*[:\-]?\s*(\d+\.?\d*)\s*(?:/\s*\d+)?', text, re.IGNORECASE)
    if match:
        val = float(match.group(1))
        if 0 < val <= 10:
            return val
    return None


def extract_projects(text: str, skills: list[str]) -> list[dict]:
    """Extract project names and associate technologies."""
    projects = []
    lines = text.split('\n')

    in_projects_section = False
    current_project = None

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        # Detect project section headers
        if any(kw in lower for kw in ['project', 'personal project', 'academic project', 'key project']):
            if len(stripped) < 40 and not any(c.isdigit() for c in stripped[:5]):
                in_projects_section = True
                continue

        # Detect end of projects section
        if in_projects_section and any(kw in lower for kw in ['experience', 'education', 'certification', 'achievement', 'skill', 'reference', 'hobby']):
            if len(stripped) < 30:
                in_projects_section = False
                if current_project:
                    projects.append(current_project)
                    current_project = None
                continue

        if in_projects_section and stripped:
            # A new project line typically starts with a bullet or is a short title
            if (stripped.startswith(('•', '-', '●', '▪', '*')) or
                (len(stripped) < 80 and stripped[0].isupper() and '.' not in stripped[:20])):
                if current_project:
                    projects.append(current_project)
                name = stripped.lstrip('•-●▪* ').strip()
                if name and len(name) > 3:
                    # Find which skills appear in this project context
                    context = stripped.lower()
                    techs = [s for s in skills if s.lower() in context]
                    current_project = {"name": name[:80], "technologies": techs}
            elif current_project:
                # Add more tech context from description lines
                for s in skills:
                    if s.lower() in stripped.lower() and s not in current_project["technologies"]:
                        current_project["technologies"].append(s)

    if current_project:
        projects.append(current_project)

    return projects[:10]  # Cap at 10 projects


def extract_experience(text: str) -> list[str]:
    """Extract work/internship experience entries."""
    entries = []
    lines = text.split('\n')
    in_experience = False

    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if any(kw in lower for kw in ['experience', 'internship', 'work history', 'employment']):
            if len(stripped) < 40:
                in_experience = True
                continue

        if in_experience and any(kw in lower for kw in ['education', 'project', 'skill', 'certification', 'achievement', 'hobby']):
            if len(stripped) < 30:
                in_experience = False
                continue

        if in_experience and stripped and len(stripped) > 10:
            if stripped.startswith(('•', '-', '●', '▪', '*')) or stripped[0].isupper():
                entry = stripped.lstrip('•-●▪* ').strip()
                if entry and len(entry) > 5:
                    entries.append(entry[:200])

    return entries[:10]


def infer_target_roles(skills: list[str]) -> list[str]:
    """Infer target internship roles from extracted skills."""
    skill_set_lower = set(s.lower() for s in skills)
    inferred = []

    for required_skills, roles in ROLE_INFERENCE_RULES:
        if {r.lower() for r in required_skills}.issubset(skill_set_lower):
            for role in roles:
                if role not in inferred:
                    inferred.append(role)

    # Always add a generic fallback if we have some skills
    if skills and "Software Engineering Intern" not in inferred:
        inferred.append("Software Engineering Intern")

    return inferred[:8]  # Cap at 8 roles


def parse_profile_deterministic(text: str) -> dict:
    """
    Comprehensive deterministic profile extraction.
    This is the primary extraction path — no LLM required.
    """
    skills = extract_skills_deterministic(text)
    name = extract_name(text)
    email = extract_email(text)
    phone = extract_phone(text)
    education = extract_education(text)
    cgpa = extract_cgpa(text)
    projects = extract_projects(text, skills)
    experience = extract_experience(text)
    inferred_roles = infer_target_roles(skills)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": sorted(s.lower() for s in skills),
        "inferred_roles": inferred_roles,
        "education": education,
        "cgpa": cgpa,
        "projects": projects,
        "experience": experience,
        "certifications": [],
    }


class ProfileResult(dict):
    """A dictionary that can also be awaited (for backward compatibility with async callers)."""
    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()


def parse_profile(text: str) -> ProfileResult:
    """
    Extract profile from resume text.
    Returns a ProfileResult dict that can be accessed synchronously or awaited.
    """
    profile = parse_profile_deterministic(text)
    skills = profile.get("skills", [])

    return ProfileResult({
        "name": profile.get("name"),
        "email": profile.get("email"),
        "phone": profile.get("phone"),
        "skills": skills,
        "inferred_roles": profile.get("inferred_roles", []),
        "education": profile.get("education", []),
        "cgpa": profile.get("cgpa"),
        "projects": profile.get("projects", []),
        "experience": profile.get("experience", []),
        "certifications": profile.get("certifications", []),
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
    """
    Validate and store resume.
    Validates synchronously, returns an awaitable coroutine for the payload.
    """
    expected_suffix = SUPPORTED_TYPES.get(content_type)
    if not expected_suffix or Path(file_name).suffix.lower() != expected_suffix:
        raise ValueError("File extension and content type must be a supported matching pair")
    if not content or len(content) > 10 * 1024 * 1024:
        raise ValueError("Resume must be between 1 byte and 10 MB")

    async def _build():
        extracted = extract_text(content, content_type)
        path = store_original(file_name, content)
        parsed_result = parse_profile(extracted)
        return {
            "resume_id": str(uuid.uuid4()),
            "student_id": student_id,
            "file_name": sanitize_filename(file_name),
            "file_path": str(path),
            "version": 1,
            "extracted_text": extracted,
            "parsed_profile": parsed_result.get("parsed_profile", parsed_result),
            "extraction_metadata": {
                "status": parsed_result.get("extraction_status", "completed"),
                "method": parsed_result.get("extraction_method", "deterministic"),
                "warnings": parsed_result.get("extraction_warnings", []),
            },
            "created_at": datetime.now(UTC).isoformat(),
        }

    return _build()
