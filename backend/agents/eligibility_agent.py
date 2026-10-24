"""
Eligibility & Ranking Agent — True LLM Semantic Evaluator

Reads the candidate's full profile (projects, skills, CGPA, strengths) and evaluates
the discovered live internships using the Groq / OpenRouter LLM Brain to produce:
- Semantic match_score (0-100%)
- Matched skills & Missing/Gap skills
- Custom, human-written rationale explaining why each specific internship fits the candidate.
"""

from __future__ import annotations

from backend.services.resume_ingestion import (
    GENERIC_BASELINE_SKILLS,
    SPECIALIZED_SKILLS,
    call_llm_json,
    extract_skills_deterministic,
)


def _normalize(text: str) -> set[str]:
    text = text.lower()
    for sep in [",", "|", "/", "(", ")", ".", "•", "●", "-"]:
        text = text.replace(sep, " ")
    return set(w.strip() for w in text.split() if len(w.strip()) > 1)


def score_opportunity(
    candidate_skills: list[str],
    candidate_roles: list[str],
    candidate_cgpa: float | None,
    opp: dict,
    project_skills: list[str] | None = None,
) -> dict:
    """
    Fast pre-scoring function (also used for unit test compatibility and initial pre-filtering
    of 60+ API jobs before deep LLM evaluation).
    """
    candidate_skills_lower = {s.lower(): s for s in candidate_skills}
    skill_priority_rank = {s.lower(): idx for idx, s in enumerate(candidate_skills)}
    project_skills_lower = {s.lower() for s in (project_skills or candidate_skills[:8])}
    specialized_lower = {s.lower() for s in SPECIALIZED_SKILLS}
    generic_lower = {s.lower() for s in GENERIC_BASELINE_SKILLS}

    explicit_reqs = opp.get("required_skills") or []
    desc_reqs = extract_skills_deterministic(f"{opp.get('role', '')} {opp.get('description', '')}")
    combined_reqs: list[str] = []
    seen_req_lower: set[str] = set()
    for r in list(explicit_reqs) + list(desc_reqs):
        r_low = r.lower().strip()
        if r_low and r_low not in seen_req_lower:
            seen_req_lower.add(r_low)
            combined_reqs.append(r)

    matched_skills: list[str] = []
    missing_skills: list[str] = []
    weighted_match_points = 0.0
    total_possible_points = 0.0

    for req_skill in combined_reqs:
        req_lower = req_skill.lower()
        skill_weight = (
            2.5 if req_lower in specialized_lower
            else (0.6 if req_lower in generic_lower else 1.5)
        )
        total_possible_points += skill_weight

        found_match = None
        matched_key = None
        for cs_low, cs_orig in candidate_skills_lower.items():
            if req_lower == cs_low or (len(req_lower) >= 3 and (req_lower in cs_low or cs_low in req_lower)):
                found_match = req_skill if req_skill[0].isupper() else cs_orig
                matched_key = cs_low
                break

        if found_match and matched_key is not None:
            if found_match not in matched_skills:
                matched_skills.append(found_match)
            rank_pos = skill_priority_rank.get(matched_key, 15)
            mult = 1.25 if (rank_pos < 8 or matched_key in project_skills_lower) else 1.0
            weighted_match_points += skill_weight * mult
        else:
            display_missing = req_skill if req_skill[0].isupper() else req_skill.title()
            if display_missing not in missing_skills:
                missing_skills.append(display_missing)

    effective_denominator = max(total_possible_points, 6.5)
    skill_match_ratio = min(weighted_match_points / effective_denominator, 1.0)

    role_bonus = 0.0
    opp_title_lower = opp.get("role", "").lower()
    opp_cat_lower = opp.get("role_category", "").lower()
    opp_tokens = _normalize(f"{opp_title_lower} {opp_cat_lower}") - {
        "intern", "internship", "engineering", "engineer", "developer", "development", "software"
    }

    for rank_idx, cr in enumerate(candidate_roles):
        cr_tokens = _normalize(cr) - {
            "intern", "internship", "engineering", "engineer", "developer", "development", "software"
        }
        if cr_tokens & opp_tokens:
            role_bonus = max(role_bonus, 0.22 if rank_idx < 2 else 0.14)

    for top_s in candidate_skills[:6]:
        if top_s.lower() not in generic_lower and top_s.lower() in opp_title_lower:
            role_bonus = min(role_bonus + 0.10, 0.28)
            break

    cgpa_bonus = 0.07 if (candidate_cgpa and candidate_cgpa >= 8.0) else (0.04 if (candidate_cgpa and candidate_cgpa >= 7.0) else 0.0)
    raw_score = (skill_match_ratio * 0.68) + role_bonus + cgpa_bonus
    match_score = min(round(raw_score * 100), 98) if matched_skills else max(round(raw_score * 100), 18)

    eligibility = "Strong Match" if match_score >= 70 else ("Partial Match" if match_score >= 45 else "Possible Fit")
    company = opp.get("company", "This company")
    role_title = opp.get("role", "this role")

    rationale = (
        f"Relevant fit for {company}'s {role_title} based on your experience with {', '.join(matched_skills[:5])}."
        if matched_skills
        else f"Entry-level alignment for {company}'s {role_title}."
    )

    return {
        **opp,
        "required_skills": combined_reqs,
        "match_score": match_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "eligibility": eligibility,
        "rationale": rationale,
        "explanation": rationale,
    }


async def run_eligibility(candidate_profile: dict, opportunities: list[dict], top_k: int = 15) -> dict:
    """
    Evaluate discovered opportunities using the LLM Brain (Groq / OpenRouter).
    1. Pre-screens the 55-75 raw API listings down to the top 18 candidates.
    2. Sends the Candidate Profile (skills, projects, strengths) + the 18 listings to the LLM
       so the agent genuinely thinks about semantic fit, scores each role, and writes a custom
       recruiter rationale for every single card.
    """
    trace_entries: list[str] = []
    skills = candidate_profile.get("skills_display") or candidate_profile.get("skills", [])
    project_skills = candidate_profile.get("project_skills") or skills[:8]
    roles = candidate_profile.get("inferred_roles", [])
    cgpa = candidate_profile.get("cgpa")
    projects = candidate_profile.get("projects", [])

    trace_entries.append(
        f"Eligibility Agent: Pre-screening {len(opportunities)} live API listings for candidate '{candidate_profile.get('name', 'Candidate')}'..."
    )

    # Step 1: Initial pre-score across all 55-75 listings so we pick the best 18 candidates for deep LLM reasoning
    pre_scored = [
        score_opportunity(skills, roles, cgpa, opp, project_skills=project_skills)
        for opp in opportunities
    ]
    pre_scored.sort(
        key=lambda x: (x.get("match_score", 0), len(x.get("matched_skills", [])), x.get("stipend_numeric", 0)),
        reverse=True,
    )
    shortlist = pre_scored[:max(top_k, 16)]

    # Step 2: Deep LLM Semantic Evaluation & Custom Rationale Generation
    proj_summary = "; ".join(
        f"{p.get('name')}: {p.get('description', '')} [{', '.join(p.get('technologies', []))}]"
        for p in projects[:5]
        if isinstance(p, dict)
    )

    listings_payload = []
    for idx, item in enumerate(shortlist):
        listings_payload.append({
            "idx": idx,
            "company": item.get("company"),
            "role": item.get("role"),
            "category": item.get("role_category"),
            "description": (item.get("description") or "")[:260],
        })

    sys_prompt = (
        "You are the Eligibility & Hiring Evaluation Agent in an autonomous career placement platform.\n"
        "You must evaluate each internship listing against this specific candidate's resume, projects, and technical stack.\n"
        "DO NOT use generic template sentences. For every listing:\n"
        "1. Think semantically about how the candidate's specific projects and skills transfer to the role.\n"
        "2. Assign a realistic `match_score` (0 to 98).\n"
        "3. Identify `matched_skills` (skills the candidate has that help in this role) and `missing_skills` (1-3 skills the candidate should learn or brush up for this role).\n"
        "4. Write a specific, insightful 1-sentence `rationale` mentioning the candidate's relevant project/skill strength for that exact company and role.\n"
        "Return ONLY valid JSON."
    )

    user_prompt = (
        f"=== CANDIDATE PROFILE ===\n"
        f"Name: {candidate_profile.get('name', 'Candidate')}\n"
        f"CGPA: {cgpa}\n"
        f"Core Strengths: {candidate_profile.get('core_strengths') or candidate_profile.get('summary', '')}\n"
        f"Skills (Ordered by Depth): {', '.join(skills[:22])}\n"
        f"Projects Built: {proj_summary or 'See skills'}\n"
        f"Target Roles: {', '.join(roles)}\n\n"
        f"=== INTERNSHIP LISTINGS TO EVALUATE ===\n{listings_payload}\n\n"
        "Return a JSON object with this exact schema:\n"
        "{\n"
        '  "evaluation_thought": "1-sentence summary of which types of roles suited this candidate best and why",\n'
        '  "evaluations": [\n'
        "    {\n"
        '      "idx": 0,\n'
        '      "match_score": 92,\n'
        '      "matched_skills": ["Skill1", "Skill2", "Skill3"],\n'
        '      "missing_skills": ["MissingSkill1"],\n'
        '      "rationale": "Specific 1-sentence reason connecting candidate projects/skills to this role"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    llm_eval, llm_source = await call_llm_json(sys_prompt, user_prompt, max_tokens=2000, temperature=0.15)

    if llm_eval and isinstance(llm_eval.get("evaluations"), list):
        eval_thought = llm_eval.get("evaluation_thought") or "Evaluated semantic project & skill fit across all listings."
        trace_entries.append(f"Eligibility Agent [{llm_source}] Thought: {eval_thought}")

        eval_map = {
            int(e["idx"]): e
            for e in llm_eval["evaluations"]
            if isinstance(e, dict) and "idx" in e and str(e["idx"]).isdigit()
        }

        for idx, item in enumerate(shortlist):
            if idx in eval_map:
                ev = eval_map[idx]
                score = int(ev.get("match_score", item["match_score"]))
                score = max(15, min(score, 98))
                item["match_score"] = score
                item["eligibility"] = (
                    "Strong Match" if score >= 70
                    else ("Partial Match" if score >= 45 else "Possible Fit")
                )
                if isinstance(ev.get("matched_skills"), list) and ev["matched_skills"]:
                    item["matched_skills"] = [str(s) for s in ev["matched_skills"][:6]]
                if isinstance(ev.get("missing_skills"), list):
                    item["missing_skills"] = [str(s) for s in ev["missing_skills"][:4]]
                if ev.get("rationale"):
                    item["rationale"] = str(ev["rationale"]).strip()
                    item["explanation"] = item["rationale"]

    # Sort final evaluated shortlist by the LLM's match_score descending
    shortlist.sort(
        key=lambda x: (x.get("match_score", 0), x.get("stipend_numeric", 0)),
        reverse=True,
    )

    final_recommendations = shortlist[:top_k]
    for rank_idx, item in enumerate(final_recommendations, start=1):
        item["rank"] = rank_idx

    strong = sum(1 for r in final_recommendations if r["eligibility"] == "Strong Match")
    partial = sum(1 for r in final_recommendations if r["eligibility"] == "Partial Match")

    trace_entries.append(
        f"Eligibility Agent: Finalized top {len(final_recommendations)} personalized matches (#1 to #{len(final_recommendations)}) — "
        f"{strong} Strong Matches, {partial} Partial Matches."
    )

    return {
        "recommendations": final_recommendations,
        "trace": trace_entries,
    }