"""
Discovery Agent — Uses LLM Reasoning to formulate a candidate-specific search
strategy and fetches live internships via the MCP OpportunityAPIConnector.
"""

from __future__ import annotations

import asyncio
from backend.connectors.api_connector import APIConnector
from backend.services.resume_ingestion import call_llm_direct, call_llm_json


async def _plan_discovery_with_llm(
    candidate_profile: dict | None,
    skills: list[str],
    inferred_roles: list[str],
    custom_query: str | None = None,
) -> tuple[list[str], str, str]:
    """
    Have the Discovery Agent LLM reason about the candidate's projects, strengths,
    and skills to design 5 high-signal API search queries.
    Returns (queries_list, strategy_thought, llm_source).
    """
    profile = candidate_profile or {}
    projects = profile.get("projects", [])
    proj_text = "; ".join(
        f"{p.get('name')}: {p.get('description', '')} ({', '.join(p.get('technologies', []))})"
        for p in projects[:5]
        if isinstance(p, dict)
    )
    strengths = profile.get("core_strengths") or profile.get("summary") or ""

    sys_prompt = (
        "You are the Discovery Agent in an autonomous multi-agent internship placement system.\n"
        "Analyze this specific candidate's projects, core strengths, and technical skills.\n"
        "Think about what makes this candidate unique compared to other students, and design 5 distinct "
        "search queries (2 to 3 words each, ending with 'intern') to query live job APIs.\n"
        "Return ONLY valid JSON."
    )

    user_prompt = (
        f"Candidate Name: {profile.get('name', 'Candidate')}\n"
        f"Recruiter Summary / Strengths: {strengths}\n"
        f"Top Weighted Skills: {', '.join(skills[:15])}\n"
        f"Candidate Projects: {proj_text or 'N/A'}\n"
        f"Inferred Role Tracks: {', '.join(inferred_roles[:6])}\n"
        + (f"User Custom Search Request: {custom_query}\n" if custom_query else "")
        + "\nReturn JSON in this exact format:\n"
        "{\n"
        '  "strategy_thought": "1-2 sentences explaining why you chose these specific search tracks for this candidate",\n'
        '  "queries": ["query 1 intern", "query 2 intern", "query 3 intern", "query 4 intern", "query 5 intern"]\n'
        "}"
    )

    plan_json, llm_source = await call_llm_json(sys_prompt, user_prompt, max_tokens=350, temperature=0.2)
    if plan_json and isinstance(plan_json.get("queries"), list):
        raw_queries = [str(q).strip().lower() for q in plan_json["queries"] if str(q).strip()]
        valid_queries = [q for q in raw_queries if 3 <= len(q) <= 40]
        thought = str(plan_json.get("strategy_thought") or "Designed queries based on candidate project stack.")
        if valid_queries:
            return valid_queries[:5], thought, llm_source

    # Fallback if offline
    fallback_queries = (profile.get("search_queries") or [])[:5]
    if not fallback_queries:
        fallback_queries = [f"{s.lower()} intern" for s in skills[:4]] or ["software engineer intern"]
    return fallback_queries, "Fallback query selection from top extracted skills.", "OfflineFallback"


async def run_discovery(
    skills: list[str],
    inferred_roles: list[str],
    location: str | None = None,
    max_results: int = 15,
    candidate_profile: dict | None = None,
    custom_query: str | None = None,
) -> dict:
    """
    Execute LLM Discovery Planning + MCP OpportunityAPIConnector fetching.
    Returns the full pool of unique internships so Eligibility Agent can evaluate all of them.
    """
    trace_entries: list[str] = []

    queries, strategy_thought, llm_source = await _plan_discovery_with_llm(
        candidate_profile=candidate_profile,
        skills=skills,
        inferred_roles=inferred_roles,
        custom_query=custom_query,
    )

    trace_entries.append(f"Discovery Agent [{llm_source}] Thought: {strategy_thought}")
    trace_entries.append(f"Discovery Agent: Planned {len(queries)} tailored API queries -> {queries}")
    trace_entries.append("Discovery Agent: Calling MCP OpportunityAPIConnector ('mcp_discover')...")

    connector = APIConnector()
    all_opportunities: list[dict] = []
    seen_ids: set[str] = set()

    try:
        mcp_response = await asyncio.wait_for(
            connector.execute(
                "mcp_discover",
                {
                    "queries": queries,
                    "location": location,
                    "max_results": max(max_results, 15),
                },
            ),
            timeout=35.0,
        )
        raw_opps = mcp_response.get("opportunities", [])
        outcomes = mcp_response.get("provider_outcomes", [])

        for outcome in outcomes:
            p_name = outcome.get("provider_name", "APIProvider")
            p_count = outcome.get("result_count", 0)
            p_status = outcome.get("status", "unknown")
            p_err = outcome.get("error")
            trace_entries.append(
                f"MCP Connector -> {p_name}: fetched {p_count} live listings (status={p_status})"
                + (f", error={p_err}" if p_err else "")
            )

        for opp in raw_opps:
            key = opp.get("source_id") or f"{opp.get('company')}:{opp.get('role')}"
            if key not in seen_ids:
                seen_ids.add(key)
                all_opportunities.append({
                    "opportunity_id": str(opp.get("source_id") or key),
                    "source": opp.get("source", "Adzuna API • MCP"),
                    "source_id": str(opp.get("source_id") or key),
                    "company": opp.get("company", "Employer"),
                    "role": opp.get("role", "Software Intern"),
                    "role_category": opp.get("role_category", "Software Engineering"),
                    "location": opp.get("location", "India"),
                    "work_mode": opp.get("work_mode", "hybrid"),
                    "stipend": opp.get("stipend", "₹35,000 / month"),
                    "stipend_numeric": int(opp.get("stipend_numeric") or 35000),
                    "duration": opp.get("duration", "3 - 6 Months"),
                    "description": opp.get("description", ""),
                    "required_skills": opp.get("required_skills", []),
                    "application_url": opp.get("application_url"),
                })

    except Exception as e:
        trace_entries.append(f"Discovery Agent: MCP API error: {e}")

    trace_entries.append(
        f"Discovery Agent: Handing off {len(all_opportunities)} unique live internships to Eligibility Agent for LLM evaluation."
    )

    return {
        "opportunities": all_opportunities,
        "trace": trace_entries,
    }