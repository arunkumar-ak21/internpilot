"""
Coordinator Agent & Autonomous LLM Brain

Orchestrates:
1. Resume Intelligence -> Discovery Strategy (MCP) -> Eligibility Evaluation pipeline.
2. Autonomous LLM intent routing & conversational reasoning in chat (no string-matching rules).
"""

from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any

from backend.agents.discovery_agent import run_discovery
from backend.agents.eligibility_agent import run_eligibility
from backend.connectors.db_connector import DatabaseConnector
from backend.core.config import get_settings
from backend.repositories.resume_repository import ResumeRepository
from backend.services.resume_ingestion import call_llm_direct, call_llm_json


@dataclass
class ConversationState:
    """Persistent session state stored via SQLite / MCP."""
    session_id: str
    trace_id: str
    target_role: str | None = None
    location: str | None = None
    minimum_stipend: int | None = None
    skills: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    opportunities: list[dict] = field(default_factory=list)
    student_id: str | None = None
    resume_id: str | None = None
    resume_profile: dict = field(default_factory=dict)
    agent_trace: list[str] = field(default_factory=list)
    chat_history: list[dict] = field(default_factory=list)


@dataclass
class CoordinatorResult:
    state: ConversationState
    action: str
    response: str
    missing_fields: list[str]
    opportunities: list[dict] = field(default_factory=list)

    def __await__(self):
        async def _identity():
            return self
        return _identity().__await__()


@dataclass
class PipelineResult:
    resume_profile: dict
    agent_trace: list[str]
    recommendations: list[dict]
    status: str


def _ensure_ranks(opportunities: list[dict]) -> list[dict]:
    """Guarantee every opportunity has a 1-based integer 'rank' (#1, #2, ...) so #None never appears."""
    for idx, opp in enumerate(opportunities, start=1):
        opp["rank"] = idx
        if not opp.get("stipend_numeric"):
            m = re.search(r"(\d[\d,]*)", str(opp.get("stipend") or ""))
            opp["stipend_numeric"] = int(m.group(1).replace(",", "")) if m else 35000
    return opportunities


async def run_pipeline(
    resume_id: str | None = None,
    student_id: str | None = None,
    location: str | None = None,
    candidate_profile: dict | None = None,
    custom_query: str | None = None,
) -> PipelineResult:
    """Execute the full Coordinator -> MCP Discovery -> LLM Eligibility pipeline."""
    trace: list[str] = []
    profile = dict(candidate_profile) if candidate_profile else {}

    trace.append("Coordinator: Starting autonomous multi-agent workflow...")

    if not profile:
        db_conn = DatabaseConnector()
        try:
            mcp_resume = await db_conn.execute("get_latest_resume", {"student_id": student_id})
            if mcp_resume and mcp_resume.get("parsed_profile"):
                profile = mcp_resume["parsed_profile"]
                trace.append("Coordinator: Loaded candidate profile via MCP SQLiteConnector.")
        except Exception:
            pass

    if not profile:
        repo = ResumeRepository(get_settings().database_url)
        if resume_id:
            profile = await repo.get_by_id(resume_id) or {}
        elif student_id:
            profile = await repo.get_latest_by_student(student_id) or {}
        if not profile:
            profile = await repo.get_latest() or {}

    skills = profile.get("skills_display") or profile.get("skills", [])
    inferred_roles = list(profile.get("inferred_roles", []))
    if custom_query:
        inferred_roles.insert(0, custom_query)

    if not skills and not custom_query:
        trace.append("Coordinator: No candidate skills found in profile.")
        return PipelineResult(
            resume_profile=profile,
            agent_trace=trace,
            recommendations=[],
            status="failed",
        )

    candidate_name = profile.get("name") or "Candidate"
    llm_src = profile.get("llm_source", "LLM")
    trace.append(
        f"Coordinator [{llm_src}]: Profile analyzed for {candidate_name} — {len(skills)} skills, "
        f"{len(profile.get('projects', []))} projects, {len(inferred_roles)} role tracks."
    )
    if profile.get("core_strengths"):
        trace.append(f"Coordinator Assessment: {profile['core_strengths']}")

    trace.append("Coordinator: Delegating search strategy to Discovery Agent...")

    try:
        discovery_result = await run_discovery(
            skills=skills,
            inferred_roles=inferred_roles,
            location=location,
            max_results=15,
            candidate_profile=profile,
            custom_query=custom_query,
        )
        trace.extend(discovery_result["trace"])
        opportunities = discovery_result["opportunities"]
    except Exception as e:
        trace.append(f"Coordinator: Discovery Agent error: {e}")
        opportunities = []

    if not opportunities:
        trace.append("Coordinator: No opportunities returned from API providers.")
        return PipelineResult(
            resume_profile=profile,
            agent_trace=trace,
            recommendations=[],
            status="no_results",
        )

    trace.append(
        f"Coordinator: Passing {len(opportunities)} live API listings to Eligibility Agent for LLM evaluation..."
    )

    try:
        eligibility_result = await run_eligibility(
            candidate_profile=profile,
            opportunities=opportunities,
        )
        trace.extend(eligibility_result["trace"])
        recommendations = _ensure_ranks(eligibility_result["recommendations"])
    except Exception as e:
        trace.append(f"Coordinator: Eligibility evaluation error: {e}")
        recommendations = _ensure_ranks(opportunities[:15])

    status = "completed" if recommendations else "no_results"
    trace.append(
        f"Coordinator: Workflow complete ({status}). Synced {len(recommendations)} ranked listings (#1 to #{len(recommendations)}) to shared memory."
    )

    return PipelineResult(
        resume_profile=profile,
        agent_trace=trace,
        recommendations=recommendations,
        status=status,
    )


def new_state(session_id: str | None = None) -> ConversationState:
    return ConversationState(
        session_id=session_id or str(uuid.uuid4()),
        trace_id=str(uuid.uuid4()),
    )


def coordinate(message: str, state: ConversationState) -> CoordinatorResult:
    """Backward-compatible deterministic coordinator for unit tests."""
    state.messages.append(message)
    lowered = message.lower()
    for phrase in ("ai/ml", "ai", "machine learning", "data science", "software", "frontend", "backend", "full-stack", "full stack"):
        if phrase in lowered:
            state.target_role = "AI/ML" if phrase in {"ai", "ai/ml", "machine learning"} else phrase.title()
            break
    if "remote" in lowered:
        state.location = "Remote"
    else:
        m = re.search(r"\bin\s+([A-Za-z ]+?)(?:\s+or\s+remote|[,.?]|$)", message, re.I)
        if m:
            state.location = m.group(1).strip().title()

    missing = []
    if not state.target_role and not state.skills:
        missing.append("target role")
    if not state.location:
        missing.append("location")

    if missing:
        return CoordinatorResult(
            state=state,
            action="clarify",
            response=f"I can help find internships. What {' and '.join(missing)} do you prefer?",
            missing_fields=missing,
            opportunities=state.opportunities,
        )

    role_desc = state.target_role or "matching"
    return CoordinatorResult(
        state=state,
        action="search",
        response=f"I have your search intent: {role_desc} internships in {state.location}. I will now search configured sources.",
        missing_fields=[],
        opportunities=state.opportunities,
    )


async def chat_with_assistant(
    message: str,
    state: ConversationState,
    resume_id: str | None = None,
    student_id: str | None = None,
) -> dict[str, Any]:
    """
    100% LLM-Driven Coordinator & Career Advisor.
    The LLM autonomously decides whether the user's message requires:
    - 'search': Running a fresh MCP API search with new role/location criteria, OR
    - 'answer': Reasoning over the candidate's resume, projects, and the 15 numbered internships (#1..#15) in memory.
    """
    state.messages.append(message)
    state.chat_history.append({"role": "user", "content": message})

    repo = ResumeRepository(get_settings().database_url)

    # 1. Ensure resume profile is in session memory
    if resume_id and (not state.resume_profile or state.resume_id != resume_id):
        loaded = await repo.get_by_id(resume_id)
        if loaded:
            state.resume_profile = loaded
            state.resume_id = loaded.get("resume_id", resume_id)
            state.student_id = loaded.get("student_id", student_id)
            state.skills = loaded.get("skills_display") or loaded.get("skills", [])
    elif not state.resume_profile:
        loaded = (
            await repo.get_latest_by_student(student_id)
            if student_id
            else None
        ) or await repo.get_latest()
        if loaded:
            state.resume_profile = loaded
            state.resume_id = loaded.get("resume_id")
            state.student_id = loaded.get("student_id")
            state.skills = loaded.get("skills_display") or loaded.get("skills", [])

    # 2. Hydrate live opportunities if empty
    if state.resume_profile and not state.opportunities:
        pipeline_res = await run_pipeline(
            resume_id=state.resume_id,
            student_id=state.student_id,
            candidate_profile=state.resume_profile,
        )
        state.opportunities = pipeline_res.recommendations
        state.agent_trace = pipeline_res.agent_trace

    state.opportunities = _ensure_ranks(state.opportunities or [])
    opps = state.opportunities
    profile = state.resume_profile or {}

    # 3. Let the Coordinator LLM Think & Decide (Answer from Context vs. Trigger New MCP Search)
    if profile or opps:
        opps_table = "\n".join(
            f"Listing #{o['rank']}:\n"
            f"  - Role: {o.get('role')}\n"
            f"  - Company: {o.get('company')}\n"
            f"  - Category: {o.get('role_category')}\n"
            f"  - Stipend: {o.get('stipend')} (Numeric Monthly INR: {o.get('stipend_numeric')})\n"
            f"  - Location & Work Mode: {o.get('location')} ({str(o.get('work_mode', 'hybrid')).upper()})\n"
            f"  - Match Score: {o.get('match_score')}% ({o.get('eligibility')})\n"
            f"  - Candidate Matched Skills: {', '.join(o.get('matched_skills', [])[:8])}\n"
            f"  - Missing Skills: {', '.join(o.get('missing_skills', [])[:5]) or 'None'}\n"
            f"  - Recruiter Rationale: {o.get('rationale', '')}\n"
            f"  - Description: {(o.get('description') or '')[:200]}"
            for o in opps[:15]
        )

        proj_summary = "; ".join(
            f"{p.get('name')}: {p.get('description', '')} ({', '.join(p.get('technologies', [])[:5])})"
            for p in profile.get("projects", [])[:5]
            if isinstance(p, dict) and p.get("name")
        )

        resume_summary = (
            f"Name: {profile.get('name', 'Candidate')}\n"
            f"CGPA: {profile.get('cgpa', 'N/A')}\n"
            f"Core Strengths: {profile.get('core_strengths') or profile.get('summary', '')}\n"
            f"Skills: {', '.join((profile.get('skills_display') or profile.get('skills', []))[:30])}\n"
            f"Target Roles: {', '.join(profile.get('inferred_roles', []))}\n"
            f"Projects: {proj_summary}"
        )

        recent_history = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in state.chat_history[-6:]
        )

        sys_prompt = (
            "You are the autonomous Coordinator & Career Advisor Agent inside InternPilot.\n"
            "You have full access to the candidate's parsed resume and the 15 ranked live internships (#1 to #15) currently on their screen.\n\n"
            "First, decide the `action`:\n"
            "- Choose `\"answer\"` if the user is asking a question about the existing #1-#15 internships (e.g., stipends, highest paying, remote roles, fullstack/backend roles, comparing #1 and #2, missing skills) OR asking about their resume/projects/career advice.\n"
            "- Choose `\"search\"` ONLY if the user explicitly asks you to fetch/search/find a new batch of internships from external APIs with a new role or city filter that isn't already on screen.\n\n"
            "When `action` is `\"answer\"`, write a comprehensive, insightful Markdown `response` that directly answers the user's question by reasoning over the exact Listing numbers (#1..#15), companies, stipends, work modes, and the candidate's resume projects.\n"
            "Return ONLY valid JSON."
        )

        user_prompt = (
            f"=== CANDIDATE RESUME ===\n{resume_summary}\n\n"
            f"=== CURRENT LIVE INTERNSHIPS ON SCREEN (#1 to #{len(opps)}) ===\n{opps_table}\n\n"
            f"=== CONVERSATION HISTORY ===\n{recent_history}\n\n"
            f"=== USER MESSAGE ===\n{message}\n\n"
            "Return JSON in this exact schema:\n"
            "{\n"
            '  "thought": "Your internal reasoning about what the user is asking and how to answer it",\n'
            '  "action": "answer", // or "search"\n'
            '  "search_query": null, // if action is "search", put the 2-3 word search query here\n'
            '  "search_location": null, // if action is "search" and a city/remote was specified\n'
            '  "response": "Your detailed Markdown response to the user"\n'
            "}"
        )

        decision_json, llm_source = await call_llm_json(sys_prompt, user_prompt, max_tokens=1000, temperature=0.2)

        if decision_json:
            thought = decision_json.get("thought") or "Analyzed user query against session memory."
            action = str(decision_json.get("action") or "answer").lower()
            state.agent_trace.append(f"Coordinator [{llm_source}] Thought: {thought}")

            # If the LLM decided to trigger a new live MCP search:
            if action == "search" and decision_json.get("search_query"):
                new_query = str(decision_json["search_query"])
                new_loc = decision_json.get("search_location") or state.location
                pipeline_res = await run_pipeline(
                    resume_id=state.resume_id,
                    student_id=state.student_id,
                    location=new_loc,
                    candidate_profile=profile,
                    custom_query=new_query,
                )
                state.opportunities = _ensure_ranks(pipeline_res.recommendations)
                state.agent_trace.extend(pipeline_res.agent_trace)
                opps = state.opportunities

                top_preview = "\n".join(
                    f"- **#{o['rank']} {o.get('role')}** at **{o.get('company')}** — {o.get('stipend')} ({o.get('match_score')}% Match, {o.get('location')})"
                    for o in opps[:5]
                )
                reply = (
                    f"{decision_json.get('response') or f'Fetched live internships for **{new_query}**:'}\n\n"
                    f"**Updated Top Matches (#1 to #{len(opps)}):**\n{top_preview}"
                )
                state.chat_history.append({"role": "assistant", "content": reply})
                return {
                    "action": "search",
                    "response": reply,
                    "state": state,
                    "opportunities": opps,
                    "resume_profile": profile,
                    "agent_trace": state.agent_trace,
                }

            # Standard analytical answer from the LLM
            reply_text = str(decision_json.get("response") or "").strip()
            if reply_text:
                state.chat_history.append({"role": "assistant", "content": reply_text})
                return {
                    "action": "answer",
                    "response": reply_text,
                    "state": state,
                    "opportunities": opps,
                    "resume_profile": profile,
                    "agent_trace": state.agent_trace,
                }

        # Direct plain-text LLM retry if JSON parsing was skipped
        raw_reply, raw_source = await call_llm_direct(sys_prompt, user_prompt, max_tokens=800)
        if raw_reply:
            state.agent_trace.append(f"Coordinator [{raw_source}]: Answered user query directly.")
            state.chat_history.append({"role": "assistant", "content": raw_reply})
            return {
                "action": "answer",
                "response": raw_reply,
                "state": state,
                "opportunities": opps,
                "resume_profile": profile,
                "agent_trace": state.agent_trace,
            }

    coord_res = coordinate(message, state)
    state.chat_history.append({"role": "assistant", "content": coord_res.response})
    return {
        "action": coord_res.action,
        "response": coord_res.response,
        "missing_fields": coord_res.missing_fields,
        "state": state,
        "opportunities": state.opportunities,
        "resume_profile": state.resume_profile,
        "agent_trace": state.agent_trace,
    }


def serialize_state(state: ConversationState) -> dict:
    return asdict(state)


def deserialize_state(payload: dict) -> ConversationState:
    valid_keys = {
        "session_id", "trace_id", "target_role", "location",
        "minimum_stipend", "skills", "messages", "opportunities",
        "student_id", "resume_id", "resume_profile", "agent_trace", "chat_history",
    }
    filtered = {k: v for k, v in payload.items() if k in valid_keys}
    if "session_id" not in filtered:
        filtered["session_id"] = str(uuid.uuid4())
    if "trace_id" not in filtered:
        filtered["trace_id"] = str(uuid.uuid4())
    return ConversationState(**filtered)