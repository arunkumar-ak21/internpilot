"""Adzuna Live API implementation of the OpportunityProvider."""

from __future__ import annotations

import re
from typing import List
import httpx

from backend.core.config import get_settings
from backend.providers.base import OpportunityProvider, RawOpportunity, SearchCriteria
from backend.services.resume_ingestion import extract_skills_deterministic


def _infer_category(title: str, description: str) -> str:
    combined = f"{title} {description}".lower()
    if any(k in combined for k in ["rag", "langchain", "llm", "generative ai", "genai", "agentic"]):
        return "Generative AI"
    if any(k in combined for k in ["computer vision", "opencv", "yolo", "image processing"]):
        return "Computer Vision"
    if any(k in combined for k in ["machine learning", "deep learning", "ai", "ml", "nlp", "data scientist"]):
        return "AI & Machine Learning"
    if any(k in combined for k in ["full stack", "fullstack", "full-stack", "react", "nextjs", "mern"]):
        return "Full-Stack Development"
    if any(k in combined for k in ["devops", "cloud", "kubernetes", "docker", "aws", "oci", "sre"]):
        return "Cloud & DevOps"
    if any(k in combined for k in ["data science", "data analyst", "pandas", "analytics", "sql"]):
        return "Data Science & Analytics"
    if any(k in combined for k in ["backend", "fastapi", "django", "spring", "api", "node", "python", "java"]):
        return "Backend Engineering"
    return "Software Engineering"


def _infer_work_mode(title: str, location: str | None, description: str) -> str:
    combined = f"{title} {location or ''} {description}".lower()
    if "remote" in combined or "work from home" in combined:
        return "remote"
    if "hybrid" in combined:
        return "hybrid"
    return "onsite"


def _estimate_stipend(title: str, description: str, category: str, sal_min: float | None, sal_max: float | None) -> tuple[str, int]:
    """Compute monthly stipend from Adzuna salary fields or realistic market tier."""
    if sal_min or sal_max:
        val = int(sal_max or sal_min)
        monthly = val // 12 if val > 120000 else val
        monthly = max(15000, min(monthly, 150000))
        return f"₹{monthly:,} / month", monthly

    # Check if stipend is written inside description text
    desc_match = re.search(r"(?:₹|Rs\.?|INR)\s*(\d{2,3}(?:,\d{3})+|\d{2}k)", description, re.IGNORECASE)
    if desc_match:
        raw = desc_match.group(1).lower().replace(",", "")
        num = int(raw.replace("k", "000")) if "k" in raw else int(raw)
        if 10000 <= num <= 150000:
            return f"₹{num:,} / month", num

    # Market rate estimation by role category so stipend comparisons work dynamically
    tier_map = {
        "Generative AI": ("₹45,000 / month (Est.)", 45000),
        "AI & Machine Learning": ("₹42,000 / month (Est.)", 42000),
        "Computer Vision": ("₹40,000 / month (Est.)", 40000),
        "Cloud & DevOps": ("₹38,000 / month (Est.)", 38000),
        "Full-Stack Development": ("₹35,000 / month (Est.)", 35000),
        "Backend Engineering": ("₹36,000 / month (Est.)", 36000),
        "Data Science & Analytics": ("₹34,000 / month (Est.)", 34000),
        "Software Engineering": ("₹32,000 / month (Est.)", 32000),
    }
    return tier_map.get(category, ("₹30,000 / month (Est.)", 30000))


def _clean_adzuna_query(raw_query: str) -> str:
    """
    Sanitize query for Adzuna API.
    Adzuna fails if given >3 keywords or special characters like '&' or '/'.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", raw_query).lower()
    stop = {"engineering", "developer", "development", "and", "or", "with", "in", "for", "the", "role", "roles"}
    tokens = [t for t in cleaned.split() if t not in stop and len(t) > 1]

    # Ensure 'intern' or 'internship' is present, plus at most 1-2 core topic words
    core_tokens = [t for t in tokens if t not in {"intern", "internship"}][:2]
    if not core_tokens:
        return "software intern"
    return " ".join(core_tokens + ["intern"])


class AdzunaProvider(OpportunityProvider):
    """Fetches real live opportunities from the Adzuna API."""

    def __init__(self, app_id: str | None = None, app_key: str | None = None):
        settings = get_settings()
        self.app_id = settings.adzuna_app_id if app_id is None else app_id
        self.app_key = settings.adzuna_app_key if app_key is None else app_key
        self._configured = bool(self.app_id and self.app_key)
        self.base_url = "https://api.adzuna.com/v1/api/jobs/in/search/1"

    async def search(self, criteria: SearchCriteria) -> List[RawOpportunity]:
        if not self._configured:
            raise ValueError("Adzuna provider is not configured with app_id and app_key.")

        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(criteria.max_results, 50),
            "what": criteria.query,
            "content-type": "application/json",
        }

        if criteria.location:
            params["where"] = criteria.location

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, timeout=12.0)
                response.raise_for_status()
                data = response.json()
            except httpx.RequestError as e:
                raise RuntimeError(f"Error fetching from Adzuna: {e}") from e
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"Adzuna API returned error status: {e.response.status_code}") from e

        raw_jobs = data.get("results", [])

        # If a specific narrow query returned 0 jobs on Adzuna, broaden to 'what_or' with 'intern'
        if not raw_jobs:
            clean_what = _clean_adzuna_query(criteria.query)
            if clean_what != "software intern":
                fallback_params = {
                    "app_id": self.app_id,
                    "app_key": self.app_key,
                    "results_per_page": 20,
                    "what_or": clean_what,
                    "what": "intern",
                    "content-type": "application/json",
                }
            async with httpx.AsyncClient() as client:
                try:
                    resp2 = await client.get(self.base_url, params=fallback_params, timeout=10.0)
                    if resp2.status_code == 200:
                        raw_jobs = resp2.json().get("results", [])
                except Exception:
                    pass

        results: List[RawOpportunity] = []
        for job in raw_jobs:
            company_name = job.get("company", {}).get("display_name", "Tech Employer")
            location_name = job.get("location", {}).get("display_name", "India")
            title = job.get("title", "Software Engineering Intern")
            desc = job.get("description", "")

            category = _infer_category(title, desc)
            work_mode = _infer_work_mode(title, location_name, desc)
            stipend_str, stipend_num = _estimate_stipend(
                title, desc, category, job.get("salary_min"), job.get("salary_max")
            )
            extracted_skills = extract_skills_deterministic(f"{title} {desc}")

            results.append(
                RawOpportunity(
                    source="adzuna",
                    source_id=str(job.get("id")),
                    company=company_name,
                    role=title,
                    location=location_name,
                    description=desc,
                    application_url=job.get("redirect_url"),
                    stipend=stipend_str,
                    stipend_numeric=stipend_num,
                    role_category=category,
                    work_mode=work_mode,
                    duration="3 - 6 Months",
                    required_skills=extracted_skills[:8],
                )
            )

        return results