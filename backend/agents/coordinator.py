"""The Dynamic LangGraph Supervisor (Advanced Multi-Agent Orchestration)."""

from __future__ import annotations
import uuid
import operator
import asyncio
import json
from dataclasses import asdict, dataclass, field
from typing import Literal, TypedDict, Annotated, Sequence, Any, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from backend.services.resume_ingestion import get_llm
from backend.repositories.resume_repository import ResumeRepository
from backend.repositories.opportunity_repository import OpportunityRepository
from backend.models.schemas import Opportunity, OpportunityMatch, EligibilityStatus, DeadlineRisk
from backend.core.config import get_settings


# ==========================================
# 1. State Definitions
# ==========================================

@dataclass
class ConversationState:
    """The persistent application state (saved to DB)."""
    session_id: str
    trace_id: str
    target_role: str | None = None
    location: str | None = None
    minimum_stipend: int | None = None
    skills: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    opportunities: list[dict] = field(default_factory=list)


class GraphState(TypedDict):
    """The internal LangGraph state passed between nodes."""
    workflow_id: str | None
    session_id: str
    student_id: str | None
    messages: Annotated[Sequence[BaseMessage], operator.add]
    candidate_profile: dict | None
    search_preferences: dict | None
    plan: str | None
    current_task: str | None
    opportunities: list[dict]
    match_results: list[dict]
    workflow_status: str | None
    errors: list[str]
    next: str

# ==========================================
# 2. Worker Agents
# ==========================================

async def profile_agent_node(state: GraphState):
    """Profile Agent: Reads the profile from DB."""
    student_id = state.get("student_id")
    if not student_id:
        return {"next": "DiscoveryAgent", "messages": [AIMessage(content="Profile Agent: No student ID provided, skipping profile load.")]}

    repo = ResumeRepository(get_settings().database_url)
    profile = await repo.get_latest_by_student(student_id)
    
    if profile:
        return {"candidate_profile": profile, "next": "DiscoveryAgent", "messages": [AIMessage(content="Profile Agent: Candidate profile loaded.")]}
    else:
        return {"candidate_profile": {}, "next": "DiscoveryAgent", "messages": [AIMessage(content="Profile Agent: No profile found for student.")]}


async def discovery_agent_node(state: GraphState):
    """Executes the Discovery Agent to invoke configured search tools."""
    from backend.providers.factory import get_provider
    from backend.providers.base import SearchCriteria
    
    llm = get_llm()
    profile = state.get("candidate_profile", {})
    skills = profile.get("skills", [])
    
    # 1. Deterministic Search Execution
    query_parts = []
    if skills:
        query_parts.append(" ".join(skills[:3]))
    else:
        query_parts.append("software engineering")
        
    query_parts.append("internship")
    query = " ".join(query_parts)
    
    provider = get_provider()
    criteria = SearchCriteria(query=query, location=None, max_results=5)
    
    opportunities = []
    try:
        search_result = await asyncio.wait_for(provider.search(criteria), timeout=25.0)
        
        opp_repo = OpportunityRepository(get_settings().database_url)
        
        for r in search_result.results:
            opp_dict = {
                "opportunity_id": str(uuid.uuid4()),
                "company": getattr(r, 'company', 'Unknown'),
                "role": getattr(r, 'role', 'Unknown'),
                "location": getattr(r, 'location', None),
                "description": getattr(r, 'description', '')[:500] + "...",
                "source": getattr(r, 'source', 'Discovery'),
                "source_id": getattr(r, 'source_id', None),
                "application_url": getattr(r, 'application_url', None)
            }
            
            # Construct standard Opportunity
            opp = Opportunity(
                opportunity_id=opp_dict["opportunity_id"],
                company=opp_dict["company"],
                role=opp_dict["role"],
                location=opp_dict["location"],
                description=getattr(r, 'description', ''),
                source=opp_dict["source"],
                source_id=opp_dict["source_id"],
                application_url=opp_dict["application_url"]
            )
            # Save opportunity to DB
            await opp_repo.save_opportunity(opp)
            opportunities.append(opp_dict)
            
    except Exception as e:
        print(f"Discovery Agent failed: {e}")
        state.get("errors", []).append(f"Discovery search failed: {e}")
        return {"opportunities": state.get("opportunities", []), "messages": [AIMessage(content=f"Discovery Agent: Search failed: {e}")], "next": "MatchingAgent"}

    if search_result.status == "search_failed":
        state.get("errors", []).append("All configured search providers failed.")
        
    return {"opportunities": opportunities, "messages": [AIMessage(content=f"Discovery Agent: Found {len(opportunities)} opportunities. Status: {search_result.status}")], "next": "MatchingAgent"}


async def matching_agent_node(state: GraphState):
    """Executes the Matching Agent to evaluate discovered opportunities against profile."""
    opportunities = state.get("opportunities", [])
    profile = state.get("candidate_profile", {})
    student_id = state.get("student_id")
    
    if not opportunities or not student_id:
        return {"next": "ResponseAgent", "messages": [AIMessage(content="Matching Agent: No opportunities or student_id to match.")]}

    opp_repo = OpportunityRepository(get_settings().database_url)
    match_results = []
    
    llm = get_llm()
    skills_context = ", ".join(profile.get("skills", []))
    
    for opp in opportunities:
        # Evaluate Match
        prompt = (
            f"You are the Eligibility Agent.\n"
            f"Candidate Skills: {skills_context}\n"
            f"Opportunity: {opp['role']} at {opp['company']}\n"
            f"Description: {opp.get('description', '')}\n\n"
            f"Determine if the candidate is a fit. Provide a brief explanation. Does it match? (YES/NO/MAYBE)"
        )
        
        try:
            response = await asyncio.wait_for(llm.ainvoke([SystemMessage(content=prompt)]), timeout=10.0)
            explanation = response.content
            
            # Simple heuristic since structured output can fail
            eligibility = EligibilityStatus.UNKNOWN
            if "YES" in explanation.upper(): eligibility = EligibilityStatus.PASS_
            elif "NO" in explanation.upper(): eligibility = EligibilityStatus.FAIL
            
            match = OpportunityMatch(
                student_id=student_id,
                opportunity_id=opp["opportunity_id"],
                eligibility=eligibility,
                explanation=explanation,
                skill_match=0.8 if eligibility == EligibilityStatus.PASS_ else 0.4
            )
            await opp_repo.save_match(match)
            match_results.append(match.model_dump())
            
        except Exception as e:
            print(f"Matching Agent LLM failed: {e}")
            # Persist an UNKNOWN match
            match = OpportunityMatch(
                student_id=student_id,
                opportunity_id=opp["opportunity_id"],
                eligibility=EligibilityStatus.UNKNOWN,
                explanation=f"Matching failed due to LLM timeout/error: {e}"
            )
            await opp_repo.save_match(match)
            match_results.append(match.model_dump())

    return {"match_results": match_results, "messages": [AIMessage(content=f"Matching Agent: Processed {len(opportunities)} matches.")], "next": "ResponseAgent"}


async def response_agent_node(state: GraphState):
    """Constructs the final response."""
    opportunities = state.get("opportunities", [])
    if opportunities:
        msg = f"I have discovered {len(opportunities)} internship opportunities and analyzed your eligibility."
    else:
        msg = "I attempted to find opportunities but none were found or an error occurred."
        
    return {"messages": [AIMessage(content=msg)], "next": "FINISH"}


class RouteSchema(BaseModel):
    """Schema forcing the LLM to output a strict routing decision."""
    next: Literal["ProfileAgent", "DiscoveryAgent", "MatchingAgent", "ResponseAgent", "FINISH"] = Field(
        description="The next worker to route to."
    )

async def coordinator_node(state: GraphState):
    """The master orchestrator that decides which agent works next."""
    # For automatic workflow: 
    if state.get("workflow_id"):
        # We just follow a strict sequence if next is not set
        if not state.get("next"):
            return {"next": "ProfileAgent"}
        return {"next": state["next"]}
        
    llm = get_llm()
    system_prompt = (
        "You are the Supervisor of an AI Internship Platform. "
        "Read the conversation history. Decide who should act next. "
        "Route to ProfileAgent to load profiles, DiscoveryAgent to find jobs, MatchingAgent to evaluate, or ResponseAgent to reply."
    )
    
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    router_llm = llm.with_structured_output(RouteSchema)
    
    try:
        decision = await asyncio.wait_for(router_llm.ainvoke(messages), timeout=10.0)
        return {"next": decision.next}
    except Exception as e:
        print(f"LLM Parsing failed: {e}")
        return {"next": "FINISH", "messages": [AIMessage(content="My AI brain is currently offline (API Error).")]}


# ==========================================
# 4. Graph Construction
# ==========================================

workflow = StateGraph(GraphState)

workflow.add_node("Coordinator", coordinator_node)
workflow.add_node("ProfileAgent", profile_agent_node)
workflow.add_node("DiscoveryAgent", discovery_agent_node)
workflow.add_node("MatchingAgent", matching_agent_node)
workflow.add_node("ResponseAgent", response_agent_node)

workflow.add_edge(START, "Coordinator")

workflow.add_conditional_edges(
    "Coordinator",
    lambda state: state.get("next", "FINISH"),
    {
        "ProfileAgent": "ProfileAgent",
        "DiscoveryAgent": "DiscoveryAgent",
        "MatchingAgent": "MatchingAgent",
        "ResponseAgent": "ResponseAgent",
        "FINISH": END
    }
)

# Enforce Automatic Pipeline
workflow.add_edge("ProfileAgent", "Coordinator")
workflow.add_edge("DiscoveryAgent", "Coordinator")
workflow.add_edge("MatchingAgent", "Coordinator")
workflow.add_edge("ResponseAgent", "Coordinator")

app = workflow.compile()


# ==========================================
# 5. API Entrypoints
# ==========================================

@dataclass
class CoordinatorResult:
    state: ConversationState
    action: str
    response: str
    missing_fields: list[str]
    opportunities: list[dict] = field(default_factory=list)


def new_state(session_id: str | None = None) -> ConversationState:
    return ConversationState(session_id=session_id or str(uuid.uuid4()), trace_id=str(uuid.uuid4()))


async def coordinate(message: str, state: ConversationState) -> CoordinatorResult:
    """Entry point for ordinary conversational requests."""
    state.messages.append(message)
    graph_messages = [HumanMessage(content=msg) for msg in state.messages[-5:]]
    
    # We must ensure we have a student_id for the ProfileAgent, but currently state doesn't have it.
    # The frontend uses session_id for anonymous chat.
    
    initial_graph_state = {
        "workflow_id": None,
        "session_id": state.session_id,
        "student_id": state.session_id, # Fallback to session_id for now
        "messages": graph_messages, 
        "next": "",
        "candidate_profile": {"skills": state.skills},
        "search_preferences": {},
        "plan": None,
        "current_task": None,
        "opportunities": state.opportunities,
        "match_results": [],
        "workflow_status": None,
        "errors": []
    }
    
    try:
        result = await asyncio.wait_for(app.ainvoke(initial_graph_state), timeout=60.0)
        final_message = result["messages"][-1].content
        action = result.get("next", "FINISH")
        opps = result.get("opportunities", [])
        if opps:
            state.opportunities = opps
    except Exception as e:
        print(f"Graph Error: {e}")
        final_message = "I encountered an error while orchestrating the agents. Please try again."
        action = "error"
        opps = []
        
    return CoordinatorResult(
        state=state,
        action=action,
        response=final_message,
        missing_fields=[],
        opportunities=state.opportunities
    )


def serialize_state(state: ConversationState) -> dict:
    return asdict(state)


def deserialize_state(payload: dict) -> ConversationState:
    return ConversationState(**payload)
