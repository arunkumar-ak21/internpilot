"""Eligibility & Ranking Agent — Scores and ranks internships against candidate profile."""

from __future__ import annotations
import re


def _normalize(text: str) -> set[str]:
    """Normalize a string into a set of lowercase tokens for matching."""
    text = text.lower()
    # Replace common separators
    for sep in [",", "|", "/", "(", ")", ".", "•", "●", "-"]:
        text = text.replace(sep, " ")
    return set(w.strip() for w in text.split() if len(w.strip()) > 1)


def _extract_required_skills_from_desc(description: str) -> list[str]:
    """Extract skill-like tokens from an internship description."""
    # Common tech keywords to look for in descriptions
    tech_keywords = {
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
        "ruby", "kotlin", "swift", "sql", "html", "css", "react", "angular",
        "vue", "node.js", "nodejs", "express", "fastapi", "flask", "django",
        "spring", "spring boot", "next.js", "postgresql", "mysql", "mongodb",
        "redis", "sqlite", "docker", "kubernetes", "k8s", "terraform", "ansible",
        "jenkins", "github actions", "ci/cd", "aws", "gcp", "azure", "linux",
        "git", "rest api", "graphql", "grpc", "websockets", "microservices",
        "machine learning", "deep learning", "pytorch", "tensorflow", "keras",
        "scikit-learn", "opencv", "yolo", "nlp", "computer vision",
        "langchain", "langgraph", "rag", "hugging face", "transformers",
        "pandas", "numpy", "apache spark", "airflow", "hadoop", "kafka",
        "react native", "flutter", "android", "ios", "firebase",
        "blockchain", "solidity", "web3", "embedded systems", "ros", "arduino",
        "haskell", "scala", "functional programming", "a/b testing",
        "data visualization", "feature engineering", "model deployment",
        "prompt engineering",
    }

    desc_lower = description.lower()
    found = []
    for kw in sorted(tech_keywords, key=len, reverse=True):
        if kw in desc_lower:
            found.append(kw)
    return found


def score_opportunity(candidate_skills: list[str], candidate_roles: list[str],
                      candidate_cgpa: float | None,
                      opp: dict) -> dict:
    """
    Score a single opportunity against the candidate profile.
    Returns enriched opportunity dict with match_score, matched_skills, missing_skills, etc.
    """
    # Normalize candidate skills for comparison
    candidate_skills_lower = set(s.lower() for s in candidate_skills)
    candidate_skills_set = set(candidate_skills)  # Original casing

    # Extract required skills from description
    required_skills_raw = _extract_required_skills_from_desc(opp.get("description", ""))

    # Match skills
    matched_skills = []
    missing_skills = []

    for req_skill in required_skills_raw:
        req_lower = req_skill.lower()
        # Check if candidate has this skill (fuzzy match)
        found = False
        for cs in candidate_skills_lower:
            if req_lower in cs or cs in req_lower:
                found = True
                # Find original casing
                for orig in candidate_skills_set:
                    if orig.lower() == cs:
                        if orig not in matched_skills:
                            matched_skills.append(orig)
                        break
                break
        if not found:
            if req_skill not in missing_skills:
                missing_skills.append(req_skill.title())

    # Compute match score
    total_required = max(len(required_skills_raw), 1)
    skill_match_ratio = len(matched_skills) / total_required

    # Role relevance bonus
    role_bonus = 0.0
    role_lower = opp.get("role", "").lower()
    for cr in candidate_roles:
        cr_tokens = _normalize(cr)
        role_tokens = _normalize(role_lower)
        overlap = cr_tokens & role_tokens
        if overlap:
            role_bonus = min(0.15, len(overlap) * 0.05)
            break

    # CGPA bonus (minor)
    cgpa_bonus = 0.0
    if candidate_cgpa and candidate_cgpa >= 7.0:
        cgpa_bonus = 0.05
    elif candidate_cgpa and candidate_cgpa >= 8.0:
        cgpa_bonus = 0.10

    # Final score: weighted combination
    raw_score = (skill_match_ratio * 0.75) + role_bonus + cgpa_bonus
    match_score = min(round(raw_score * 100), 100)

    # Eligibility status
    if match_score >= 70:
        eligibility = "Strong Match"
    elif match_score >= 45:
        eligibility = "Partial Match"
    elif match_score >= 25:
        eligibility = "Possible Fit"
    else:
        eligibility = "Low Match"

    # Generate rationale
    if matched_skills:
        skills_str = ", ".join(matched_skills[:5])
        rationale = f"Your skills in {skills_str} align well with this role."
    else:
        rationale = "Limited direct skill overlap detected."

    if missing_skills:
        missing_str = ", ".join(missing_skills[:3])
        rationale += f" Consider strengthening: {missing_str}."

    return {
        **opp,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "eligibility": eligibility,
        "rationale": rationale,
    }


async def run_eligibility(candidate_profile: dict, opportunities: list[dict]) -> dict:
    """
    Evaluate all opportunities against the candidate profile.
    Returns ranked results and trace entries.
    """
    trace_entries = []
    skills = candidate_profile.get("skills", [])
    roles = candidate_profile.get("inferred_roles", [])
    cgpa = candidate_profile.get("cgpa")

    trace_entries.append(f"Eligibility Agent: Evaluating {len(opportunities)} opportunities against {len(skills)} candidate skills.")

    scored_results = []
    for opp in opportunities:
        result = score_opportunity(skills, roles, cgpa, opp)
        scored_results.append(result)

    # Sort by match_score descending
    scored_results.sort(key=lambda x: x["match_score"], reverse=True)

    # Summary stats
    strong = sum(1 for r in scored_results if r["eligibility"] == "Strong Match")
    partial = sum(1 for r in scored_results if r["eligibility"] == "Partial Match")

    trace_entries.append(f"Eligibility Agent: Ranked {len(scored_results)} internships — {strong} Strong Matches, {partial} Partial Matches.")

    return {
        "recommendations": scored_results,
        "trace": trace_entries,
    }
