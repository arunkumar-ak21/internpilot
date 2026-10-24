"""Rich curated internship provider with stipends, role categories, work modes, and required skills."""

from __future__ import annotations

import re
from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria

# 25+ diverse, realistic tech internships with full stipend, category, work_mode, and skill metadata
CURATED_INTERNSHIPS: list[RawOpportunity] = [
    RawOpportunity(
        source="mock",
        source_id="cur-001",
        company="Google DeepMind",
        role="AI/ML Research Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Work on cutting-edge machine learning, reinforcement learning, and deep neural network architectures. "
            "Requirements: Python, PyTorch, TensorFlow, Machine Learning, Deep Learning, Neural Networks. "
            "Experience with NLP, Q-Learning, or Computer Vision is highly valued."
        ),
        application_url="https://careers.google.com/internships",
        stipend="₹1,10,000 / month",
        stipend_numeric=110000,
        role_category="AI / ML",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "NLP", "Computer Vision"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-002",
        company="Microsoft Research",
        role="Generative AI & Agentic Systems Intern",
        location="Hyderabad, India (Hybrid)",
        description=(
            "Build and evaluate large language models, multi-agent systems, and RAG pipelines. "
            "Requirements: Python, RAG, LangChain, LangGraph, ChromaDB, Ollama, Generative AI, FastAPI."
        ),
        application_url="https://careers.microsoft.com/internships",
        stipend="₹95,000 / month",
        stipend_numeric=95000,
        role_category="Generative AI / Agentic AI",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "RAG", "LangChain", "LangGraph", "ChromaDB", "Ollama", "Generative AI", "FastAPI"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-003",
        company="NVIDIA",
        role="Computer Vision & Deep Learning Intern",
        location="Pune, India (Hybrid)",
        description=(
            "Work on real-time object detection, road hazard perception, and image segmentation models. "
            "Requirements: Python, C++, OpenCV, YOLO, Computer Vision, Deep Learning, PyTorch."
        ),
        application_url="https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
        stipend="₹85,000 / month",
        stipend_numeric=85000,
        role_category="Computer Vision & AI",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "C++", "OpenCV", "YOLO", "Computer Vision", "Deep Learning", "PyTorch"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-004",
        company="Flipkart",
        role="Backend Software Engineering Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Build high-concurrency backend microservices and real-time APIs for e-commerce scale. "
            "Requirements: Python, Java, FastAPI, REST API, WebSockets, PostgreSQL, Docker, System Design."
        ),
        application_url="https://www.flipkartcareers.com/internships",
        stipend="₹75,000 / month",
        stipend_numeric=75000,
        role_category="Backend Engineering",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "Java", "FastAPI", "REST API", "WebSockets", "PostgreSQL", "Docker", "System Design"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-005",
        company="Razorpay",
        role="Full-Stack Developer Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Develop end-to-end payment dashboard features, real-time merchant analytics, and developer APIs. "
            "Requirements: React, JavaScript, TypeScript, Node.js, FastAPI, SQL, Supabase, REST API."
        ),
        application_url="https://razorpay.com/careers",
        stipend="₹65,000 / month",
        stipend_numeric=65000,
        role_category="Full-Stack Development",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["React", "JavaScript", "TypeScript", "Node.js", "FastAPI", "SQL", "Supabase", "REST API"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-006",
        company="Amazon (AWS)",
        role="Cloud & DevOps Engineering Intern",
        location="Remote (India)",
        description=(
            "Design and automate cloud-native infrastructure and CI/CD pipelines. "
            "Requirements: Docker, Kubernetes, Linux, CI/CD, Python, AWS, Git, Computer Networks."
        ),
        application_url="https://amazon.jobs/internships",
        stipend="₹80,000 / month",
        stipend_numeric=80000,
        role_category="DevOps & Cloud",
        work_mode="remote",
        duration="6 Months",
        required_skills=["Docker", "Kubernetes", "Linux", "CI/CD", "Python", "AWS", "Git", "Computer Networks"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-007",
        company="Oracle Cloud (OCI)",
        role="Cloud Infrastructure & AI Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Develop cloud infrastructure services and AI foundation integrations on Oracle Cloud Infrastructure. "
            "Requirements: Java, Python, Oracle Cloud Infrastructure, Docker, Kubernetes, Linux, CI/CD, SQL."
        ),
        application_url="https://www.oracle.com/careers/students-grads/",
        stipend="₹70,000 / month",
        stipend_numeric=70000,
        role_category="DevOps & Cloud",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Java", "Python", "Oracle Cloud Infrastructure", "Docker", "Kubernetes", "Linux", "CI/CD", "SQL"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-008",
        company="Swiggy",
        role="Machine Learning & Data Science Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Build ML models for ETA prediction, reinforcement learning routing, and demand forecasting. "
            "Requirements: Python, Machine Learning, Scikit-Learn, Pandas, NumPy, SQL, Random Forest, Q-Learning."
        ),
        application_url="https://careers.swiggy.com",
        stipend="₹60,000 / month",
        stipend_numeric=60000,
        role_category="AI / ML",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "Machine Learning", "Scikit-Learn", "Pandas", "NumPy", "SQL", "Random Forest"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-009",
        company="Zerodha",
        role="Real-Time Backend Systems Intern",
        location="Bangalore, India (Remote)",
        description=(
            "Build low-latency streaming backends, WebSocket gateways, and portfolio analytics services. "
            "Requirements: Python, FastAPI, WebSockets, SQL, Linux, Docker, Redis, TCP/IP."
        ),
        application_url="https://zerodha.com/careers",
        stipend="₹65,000 / month",
        stipend_numeric=65000,
        role_category="Backend Engineering",
        work_mode="remote",
        duration="6 Months",
        required_skills=["Python", "FastAPI", "WebSockets", "SQL", "Linux", "Docker", "TCP/IP"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-010",
        company="Postman",
        role="Full-Stack API Platform Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Build collaborative developer tools for API testing and agent workflows. "
            "Requirements: JavaScript, TypeScript, React, Node.js, REST API, Git, Docker."
        ),
        application_url="https://www.postman.com/company/careers",
        stipend="₹60,000 / month",
        stipend_numeric=60000,
        role_category="Full-Stack Development",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["JavaScript", "TypeScript", "React", "Node.js", "REST API", "Git", "Docker"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-011",
        company="Zomato",
        role="Data Science & Analytics Intern",
        location="Remote",
        description=(
            "Analyze user ordering patterns and build predictive ML models. "
            "Requirements: Python, Pandas, NumPy, Scikit-Learn, SQL, Machine Learning, Data Analysis."
        ),
        application_url="https://www.zomato.com/careers",
        stipend="₹50,000 / month",
        stipend_numeric=50000,
        role_category="Data Science",
        work_mode="remote",
        duration="3 - 6 Months",
        required_skills=["Python", "Pandas", "NumPy", "Scikit-Learn", "SQL", "Machine Learning", "Data Analysis"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-012",
        company="PhonePe",
        role="DevOps & Platform Engineering Intern",
        location="Bangalore, India (Onsite)",
        description=(
            "Automate container orchestration, deployment pipelines, and Linux server reliability. "
            "Requirements: Docker, Kubernetes, Linux, CI/CD, Python, Git, Bash."
        ),
        application_url="https://www.phonepe.com/careers",
        stipend="₹65,000 / month",
        stipend_numeric=65000,
        role_category="DevOps & Cloud",
        work_mode="onsite",
        duration="6 Months",
        required_skills=["Docker", "Kubernetes", "Linux", "CI/CD", "Python", "Git", "Bash"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-013",
        company="Atlassian",
        role="Full-Stack / Frontend Engineering Intern",
        location="Bangalore, India (Remote)",
        description=(
            "Build interactive UI components and backend integrations for Jira and Confluence. "
            "Requirements: React, JavaScript, TypeScript, HTML, CSS, REST API, Git."
        ),
        application_url="https://www.atlassian.com/company/careers/internships",
        stipend="₹85,000 / month",
        stipend_numeric=85000,
        role_category="Full-Stack Development",
        work_mode="remote",
        duration="6 Months",
        required_skills=["React", "JavaScript", "TypeScript", "HTML", "CSS", "REST API", "Git"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-014",
        company="TCS Research & Innovation",
        role="AI & NLP Research Intern",
        location="Bangalore / Mumbai, India (Hybrid)",
        description=(
            "Work on applied NLP, conversational AI systems, and enterprise knowledge retrieval. "
            "Requirements: Python, NLP, Machine Learning, Deep Learning, RAG, SQL, Java."
        ),
        application_url="https://www.tcs.com/careers/internships",
        stipend="₹40,000 / month",
        stipend_numeric=40000,
        role_category="AI / ML",
        work_mode="hybrid",
        duration="3 - 6 Months",
        required_skills=["Python", "NLP", "Machine Learning", "Deep Learning", "RAG", "SQL", "Java"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-015",
        company="Infosys Springboard",
        role="Python & AI Backend Developer Intern",
        location="Remote (India)",
        description=(
            "Develop FastAPI backend services, LLM chatbots, and automated testing pipelines. "
            "Requirements: Python, FastAPI, SQL, REST API, Git, Machine Learning."
        ),
        application_url="https://www.infosys.com/careers/internship.html",
        stipend="₹30,000 / month",
        stipend_numeric=30000,
        role_category="Backend Engineering",
        work_mode="remote",
        duration="3 Months",
        required_skills=["Python", "FastAPI", "SQL", "REST API", "Git", "Machine Learning"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-016",
        company="Ola Electric (Krutrim AI)",
        role="AI, IoT & Embedded Systems Intern",
        location="Bangalore, India (Onsite)",
        description=(
            "Work on thermal sensor anomaly detection, ESP32 edge telemetry, and AI diagnostics. "
            "Requirements: Python, C, C++, IoT, ESP32, Embedded Systems, Computer Vision."
        ),
        application_url="https://olaelectric.com/careers",
        stipend="₹45,000 / month",
        stipend_numeric=45000,
        role_category="IoT & Embedded Systems",
        work_mode="onsite",
        duration="6 Months",
        required_skills=["Python", "C", "C++", "IoT", "ESP32", "Embedded Systems", "Computer Vision"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-017",
        company="Qualcomm",
        role="Systems & Multimedia Streaming Intern",
        location="Hyderabad, India (Hybrid)",
        description=(
            "Build low-latency wireless display streaming and embedded system drivers. "
            "Requirements: C, C++, Java, Python, WebRTC, TCP/IP, Linux, Android Development."
        ),
        application_url="https://qualcomm.wd5.myworkdayjobs.com",
        stipend="₹70,000 / month",
        stipend_numeric=70000,
        role_category="Systems & Embedded",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["C", "C++", "Java", "Python", "WebRTC", "TCP/IP", "Linux", "Android Development"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-018",
        company="Uber",
        role="Full-Stack & Backend Engineering Intern",
        location="Bangalore / Hyderabad, India (Hybrid)",
        description=(
            "Build real-time dispatch dashboards and scalable backend services. "
            "Requirements: Java, Python, React, Node.js, SQL, Docker, Microservices."
        ),
        application_url="https://www.uber.com/careers/",
        stipend="₹90,000 / month",
        stipend_numeric=90000,
        role_category="Full-Stack Development",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Java", "Python", "React", "Node.js", "SQL", "Docker", "Microservices"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-019",
        company="Myntra",
        role="Computer Vision & Recommendation Intern",
        location="Bangalore, India (Hybrid)",
        description=(
            "Build visual search, outfit detection, and personalized recommendation engines. "
            "Requirements: Python, Deep Learning, Computer Vision, OpenCV, PyTorch, Machine Learning."
        ),
        application_url="https://www.myntra.com/careers",
        stipend="₹60,000 / month",
        stipend_numeric=60000,
        role_category="Computer Vision & AI",
        work_mode="hybrid",
        duration="6 Months",
        required_skills=["Python", "Deep Learning", "Computer Vision", "OpenCV", "PyTorch", "Machine Learning"],
    ),
    RawOpportunity(
        source="mock",
        source_id="cur-020",
        company="Freshworks",
        role="SaaS Backend & AI Integration Intern",
        location="Chennai / Remote, India",
        description=(
            "Develop multi-tenant backend APIs and AI customer support copilot workflows. "
            "Requirements: Python, Java, FastAPI, REST API, SQL, Docker, Generative AI."
        ),
        application_url="https://www.freshworks.com/company/careers",
        stipend="₹45,000 / month",
        stipend_numeric=45000,
        role_category="Backend Engineering",
        work_mode="remote",
        duration="6 Months",
        required_skills=["Python", "Java", "FastAPI", "REST API", "SQL", "Docker", "Generative AI"],
    ),
]


def _compute_relevance(opp: RawOpportunity, query_lower: str, candidate_skills: list[str]) -> float:
    """Compute a relevance score (0.0-1.0) for ranking discovered internships."""
    score = 0.0
    desc_words = set(re.findall(r"\b[a-zA-Z0-9+#.-]+\b", opp.description.lower()))
    role_words = set(re.findall(r"\b[a-zA-Z0-9+#.-]+\b", opp.role.lower()))
    cat_words = set(re.findall(r"\b[a-zA-Z0-9+#.-]+\b", opp.role_category.lower()))
    req_skills_lower = {s.lower() for s in opp.required_skills}

    # Query token match
    for word in query_lower.split():
        if len(word) >= 2:
            if word in role_words or word in cat_words:
                score += 0.25
            elif word in req_skills_lower or word in desc_words:
                score += 0.12

    # Skill overlap
    for skill in candidate_skills:
        s_low = skill.lower()
        if s_low in req_skills_lower:
            score += 0.2
        elif s_low in role_words:
            score += 0.18
        elif s_low in desc_words:
            score += 0.1

    return min(score, 1.0)


class MockOpportunityProvider(OpportunityProvider):
    """Rich curated provider that filters and ranks based on candidate context."""

    async def search(self, criteria: SearchCriteria) -> list[RawOpportunity]:
        query_lower = criteria.query.lower()

        stop_words = {"internship", "intern", "developer", "engineering", "engineer", "and", "the", "for", "in"}
        candidate_skills = [
            w.strip()
            for w in re.split(r"[\s,|/]+", query_lower)
            if len(w.strip()) >= 1 and w.strip() not in stop_words
        ]

        pool = list(CURATED_INTERNSHIPS)
        if criteria.location:
            loc_lower = criteria.location.lower().strip()
            loc_matched = [
                opp
                for opp in pool
                if loc_lower in (opp.location or "").lower() or loc_lower in opp.work_mode.lower()
            ]
            if loc_matched:
                pool = loc_matched

        scored = []
        for opp in pool:
            relevance = _compute_relevance(opp, query_lower, candidate_skills)
            scored.append((relevance, opp))

        scored.sort(key=lambda x: (x[0], x[1].stipend_numeric), reverse=True)

        relevant = [opp for rel, opp in scored if rel > 0.05]
        if not relevant:
            relevant = [opp for _, opp in scored]

        return relevant[: criteria.max_results]