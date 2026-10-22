"""Rich curated internship provider for fallback/demo. Dynamically filters by candidate skills."""

from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria

# 25+ diverse, realistic tech internships
CURATED_INTERNSHIPS = [
    RawOpportunity(source="mock", source_id="cur-001", company="Google DeepMind", role="AI/ML Research Intern",
        location="Bangalore, India (Hybrid)", description="Work on cutting-edge machine learning research. Requirements: Python, PyTorch/TensorFlow, Deep Learning, Neural Networks. Experience with NLP or Computer Vision preferred.",
        application_url="https://careers.google.com/internships"),
    RawOpportunity(source="mock", source_id="cur-002", company="Microsoft Research", role="Generative AI Intern",
        location="Hyderabad, India (Hybrid)", description="Build and evaluate large language models and RAG systems. Requirements: Python, LangChain, Transformers, Hugging Face, prompt engineering. Familiarity with Azure ML a plus.",
        application_url="https://careers.microsoft.com/internships"),
    RawOpportunity(source="mock", source_id="cur-003", company="Amazon (AWS)", role="Cloud Engineering Intern",
        location="Remote (India)", description="Design and implement cloud-native solutions on AWS. Requirements: AWS, Docker, Kubernetes, Terraform, CI/CD, Python or Go. Linux experience required.",
        application_url="https://amazon.jobs/internships"),
    RawOpportunity(source="mock", source_id="cur-004", company="Flipkart", role="Backend Engineering Intern",
        location="Bangalore, India", description="Build scalable backend services for India's largest e-commerce platform. Requirements: Java or Python, Spring Boot or FastAPI, PostgreSQL, Redis, microservices, REST API.",
        application_url="https://www.flipkartcareers.com/internships"),
    RawOpportunity(source="mock", source_id="cur-005", company="Razorpay", role="Full-Stack Developer Intern",
        location="Bangalore, India", description="Develop payment dashboard features end-to-end. Requirements: React, TypeScript, Node.js, PostgreSQL, REST API. Experience with fintech or payments a plus.",
        application_url="https://razorpay.com/careers"),
    RawOpportunity(source="mock", source_id="cur-006", company="NVIDIA", role="Computer Vision Intern",
        location="Pune, India (Hybrid)", description="Work on real-time object detection and image segmentation. Requirements: Python, OpenCV, YOLO, PyTorch, Deep Learning, CUDA. GPU programming experience preferred.",
        application_url="https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"),
    RawOpportunity(source="mock", source_id="cur-007", company="Zomato", role="Data Science Intern",
        location="Remote", description="Analyze user behavior and build recommendation models. Requirements: Python, Pandas, NumPy, Scikit-Learn, SQL, data visualization. Machine Learning knowledge preferred.",
        application_url="https://www.zomato.com/careers"),
    RawOpportunity(source="mock", source_id="cur-008", company="Atlassian", role="Frontend Developer Intern",
        location="Bangalore, India (Hybrid)", description="Build UI components for Jira/Confluence. Requirements: React, TypeScript, CSS, responsive design, REST API. Testing with Jest preferred.",
        application_url="https://www.atlassian.com/company/careers/internships"),
    RawOpportunity(source="mock", source_id="cur-009", company="PhonePe", role="DevOps Engineering Intern",
        location="Bangalore, India", description="Automate CI/CD pipelines and manage container orchestration. Requirements: Docker, Kubernetes, Jenkins, GitHub Actions, Linux, Python, Terraform.",
        application_url="https://www.phonepe.com/careers"),
    RawOpportunity(source="mock", source_id="cur-010", company="Infosys (Springboard)", role="Python Developer Intern",
        location="Remote (India)", description="Develop backend APIs and automation tools. Requirements: Python, FastAPI or Django, SQL, Git. Knowledge of REST APIs and databases required.",
        application_url="https://www.infosys.com/careers/internship.html"),
    RawOpportunity(source="mock", source_id="cur-011", company="TCS Research", role="NLP Research Intern",
        location="Mumbai, India", description="Work on text classification, named entity recognition, and sentiment analysis. Requirements: Python, NLP, Hugging Face Transformers, spaCy, NLTK.",
        application_url="https://www.tcs.com/careers/internships"),
    RawOpportunity(source="mock", source_id="cur-012", company="Swiggy", role="Machine Learning Intern",
        location="Bangalore, India (Hybrid)", description="Build ML models for delivery time prediction and demand forecasting. Requirements: Python, Scikit-Learn, PyTorch, Pandas, feature engineering, SQL.",
        application_url="https://careers.swiggy.com"),
    RawOpportunity(source="mock", source_id="cur-013", company="Oracle Cloud (OCI)", role="Cloud Infrastructure Intern",
        location="Bangalore, India (Hybrid)", description="Develop cloud infrastructure services on Oracle Cloud. Requirements: Java or Go, Docker, Kubernetes, Linux, networking fundamentals, CI/CD.",
        application_url="https://www.oracle.com/careers/students-grads/"),
    RawOpportunity(source="mock", source_id="cur-014", company="Postman", role="API Platform Intern",
        location="Bangalore, India", description="Build developer tools for API testing. Requirements: JavaScript/TypeScript, Node.js, React, REST API, GraphQL. Open-source contribution experience valued.",
        application_url="https://www.postman.com/company/careers"),
    RawOpportunity(source="mock", source_id="cur-015", company="Zerodha", role="Backend Golang Intern",
        location="Bangalore, India (Remote-first)", description="Build high-performance trading infrastructure. Requirements: Go, Python, PostgreSQL, Redis, Linux, WebSockets, microservices.",
        application_url="https://zerodha.com/careers"),
    RawOpportunity(source="mock", source_id="cur-016", company="Qualcomm", role="Embedded Systems Intern",
        location="Hyderabad, India", description="Work on embedded firmware for 5G chipsets. Requirements: C, C++, embedded systems, RTOS, Linux kernel, ARM architecture.",
        application_url="https://qualcomm.wd5.myworkdayjobs.com"),
    RawOpportunity(source="mock", source_id="cur-017", company="CRED", role="React Native Mobile Intern",
        location="Bangalore, India", description="Build mobile features for the CRED app. Requirements: React Native, TypeScript, Redux, REST API, mobile UI/UX, Git.",
        application_url="https://careers.cred.club"),
    RawOpportunity(source="mock", source_id="cur-018", company="Adobe", role="Data Engineering Intern",
        location="Noida, India (Hybrid)", description="Build ETL pipelines and data warehouse solutions. Requirements: Python, Apache Spark, SQL, Airflow, AWS/GCP, data modeling.",
        application_url="https://www.adobe.com/careers/university.html"),
    RawOpportunity(source="mock", source_id="cur-019", company="Freshworks", role="SaaS Backend Intern",
        location="Chennai, India", description="Develop multi-tenant SaaS backend services. Requirements: Python or Ruby, Django or Rails, PostgreSQL, Redis, REST API, microservices.",
        application_url="https://www.freshworks.com/company/careers"),
    RawOpportunity(source="mock", source_id="cur-020", company="Ola Electric", role="IoT & Robotics Intern",
        location="Bangalore, India", description="Work on IoT sensor integration and robotics for EV manufacturing. Requirements: Python, C++, ROS, Arduino, embedded systems, IoT protocols.",
        application_url="https://olaelectric.com/careers"),
    RawOpportunity(source="mock", source_id="cur-021", company="Polygon Labs", role="Blockchain Developer Intern",
        location="Remote (Global)", description="Build smart contracts and DeFi protocols. Requirements: Solidity, JavaScript, Web3.js, blockchain fundamentals, Ethereum, testing frameworks.",
        application_url="https://polygon.technology/careers"),
    RawOpportunity(source="mock", source_id="cur-022", company="Samsung R&D", role="Android Developer Intern",
        location="Bangalore, India", description="Develop features for Samsung Galaxy devices. Requirements: Kotlin, Java, Android SDK, Jetpack Compose, Firebase, Git.",
        application_url="https://www.samsung.com/in/aboutsamsung/careers/"),
    RawOpportunity(source="mock", source_id="cur-023", company="Uber", role="Full-Stack Engineering Intern",
        location="Hyderabad, India (Hybrid)", description="Build rider and driver platform features. Requirements: React, Node.js, Go or Java, PostgreSQL, GraphQL, Docker, microservices.",
        application_url="https://www.uber.com/careers/"),
    RawOpportunity(source="mock", source_id="cur-024", company="Myntra", role="ML/RecSys Intern",
        location="Bangalore, India", description="Build fashion recommendation and visual search systems. Requirements: Python, deep learning, recommendation systems, computer vision, PyTorch, A/B testing.",
        application_url="https://www.myntra.com/careers"),
    RawOpportunity(source="mock", source_id="cur-025", company="Juspay", role="Haskell/Functional Programming Intern",
        location="Bangalore, India", description="Build payment processing engines using functional programming. Requirements: Haskell or Scala, PostgreSQL, Docker, functional programming, Git.",
        application_url="https://juspay.in/careers"),
]


def _compute_relevance(opp: RawOpportunity, query_lower: str, candidate_skills: list[str]) -> float:
    """Compute a relevance score (0.0-1.0) for ranking."""
    score = 0.0
    import re
    desc_words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', opp.description.lower()))
    role_words = set(re.findall(r'\b[a-zA-Z0-9+#.-]+\b', opp.role.lower()))

    # Query match
    for word in query_lower.split():
        if len(word) > 2:
            if word in role_words:
                score += 0.3
            elif word in desc_words:
                score += 0.1

    # Skill overlap
    skills_lower = [s.lower() for s in candidate_skills]
    for skill in skills_lower:
        if skill in role_words:
            score += 0.2
        elif skill in desc_words:
            score += 0.15

    return min(score, 1.0)


class MockOpportunityProvider(OpportunityProvider):
    """Rich curated provider that filters and ranks based on candidate context."""

    async def search(self, criteria: SearchCriteria) -> list[RawOpportunity]:
        query_lower = criteria.query.lower()

        # Extract candidate skills from query tokens for better matching
        candidate_skills = [w.strip() for w in query_lower.replace("internship", "").split() if len(w.strip()) > 1]

        pool = CURATED_INTERNSHIPS
        if criteria.location:
            loc_lower = criteria.location.lower().strip()
            loc_matched = [opp for opp in pool if loc_lower in (opp.location or "").lower()]
            if loc_matched:
                pool = loc_matched

        # Score internships in pool
        scored = []
        for opp in pool:
            relevance = _compute_relevance(opp, query_lower, candidate_skills)
            scored.append((relevance, opp))

        # Sort by relevance descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return relevant items (relevance > 0.05); if none, fallback to top scored
        relevant = [opp for rel, opp in scored if rel > 0.05]
        if not relevant:
            relevant = [opp for _, opp in scored]

        return relevant[: criteria.max_results]
