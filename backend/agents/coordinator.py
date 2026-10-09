"""The Dynamic LangGraph Supervisor (Advanced Multi-Agent Orchestration)."""

from __future__ import annotations

import uuid
import operator
import asyncio
from dataclasses import asdict, dataclass, field
from typing import Literal, TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from backend.services.resume_ingestion import get_llm


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
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    skills: list[str]
    target_role: str | None
    location: str | None
    opportunities: list[dict]

# ==========================================
# 2. Worker Agents (Deterministic Nodes)
# ==========================================

async def discovery_node(state: GraphState):
    """Executes the Discovery Agent in a fixed, deterministic pipeline."""
    from backend.providers.factory import get_provider
    from backend.providers.base import SearchCriteria
    from langchain_core.messages import AIMessage
    
    llm = get_llm()
    skills = state.get("skills", [])
    target_role = state.get("target_role")
    location = state.get("location")
    
    # 1. Deterministic Search Execution
    query_parts = []
    if target_role:
        query_parts.append(target_role)
    elif skills:
        query_parts.append(" ".join(skills[:3]))
    else:
        query_parts.append("software engineering")
        
    query_parts.append("internship")
    query = " ".join(query_parts)
    
    provider = get_provider()
    criteria = SearchCriteria(query=query, location=location, max_results=5)
    
    try:
        raw_results = await provider.search(criteria)
        opportunities = []
        for r in raw_results:
            opp_dict = {
                "company": r.company,
                "role": r.role,
                "location": r.location,
                "description": r.description[:500] + "..." if len(r.description) > 500 else r.description,
                "source": r.source,
                "source_id": r.source_id,
                "application_url": r.application_url
            }
            opportunities.append(opp_dict)
    except Exception as e:
        opportunities = []
        error_msg = f"Search failed: {e}"
        print(error_msg)
        return {"messages": [AIMessage(content=f"I tried searching for {query}, but the search provider failed or is unavailable.")], "opportunities": []}

    if not opportunities:
        return {"messages": [AIMessage(content=f"I searched for '{query}' but couldn't find any matching opportunities right now.")], "opportunities": []}

    # 2. Synthesis (LLM Call)
    skills_context = f"The user has the following skills: {', '.join(skills)}." if skills else ""
    opps_text = "\n".join([f"- {o['role']} at {o['company']} ({o['location']})" for o in opportunities])
    prompt = (
        f"You are the Discovery Agent. {skills_context}\n"
        f"I searched the web for '{query}' and found these {len(opportunities)} opportunities:\n\n{opps_text}\n\n"
        "Synthesize these findings into a short conversational summary, highlighting why they match."
    )
    
    from langchain_core.messages import SystemMessage
    response = await asyncio.wait_for(
        llm.ainvoke([SystemMessage(content=prompt)] + list(state["messages"])),
        timeout=15.0
    )
    
    return {"messages": [response], "opportunities": opportunities}



async def eligibility_node(state: GraphState):
    """Executes the Eligibility Agent in a fixed, deterministic pipeline."""
    llm = get_llm()
    skills = state.get("skills", [])
    opportunities = state.get("opportunities", [])
    
    skills_context = f"The user has the following skills: {', '.join(skills)}." if skills else ""
    opps_context = ""
    if opportunities:
        opps_text = "\n".join([f"- {o['role']} at {o['company']}" for o in opportunities])
        opps_context = f"Here are the currently discovered opportunities:\n{opps_text}\n"
    
    prompt = (
        f"You are the Eligibility Agent. {skills_context}\n{opps_context}\n"
        "Your responsibility is to evaluate if the candidate is a good fit "
        "for the jobs currently discussed. Be highly analytical. Highlight missing skills. "
        "Return your evaluation as a conversational response."
    )
    
    from langchain_core.messages import SystemMessage
    response = await asyncio.wait_for(
        llm.ainvoke([SystemMessage(content=prompt)] + list(state["messages"])),
        timeout=15.0
    )
    return {"messages": [response]}


class RouteSchema(BaseModel):
    """Schema forcing the LLM to output a strict routing decision."""
    next: Literal["Discovery", "Eligibility", "FINISH"] = Field(
        description="The next worker to route to. Use FINISH if the user's request has been fully addressed."
    )


async def supervisor_node(state: GraphState):
    """The master orchestrator that decides which agent works next."""
    llm = get_llm()
    
    skills = state.get("skills", [])
    skills_context = f"The user's skills are: {', '.join(skills)}." if skills else "No skills provided yet."
    
    system_prompt = (
        "You are the Supervisor of an AI Internship Platform. "
        "You orchestrate a team of workers: 'Discovery' (finds jobs) and 'Eligibility' (evaluates fit). "
        f"{skills_context}\n"
        "Read the conversation history. Decide who should act next. "
        "If the user is asking to find jobs, route to Discovery. "
        "If the user is asking if they are qualified or asking about their skills, route to Eligibility (or handle it yourself). "
        "If the request is fully answered, route to FINISH."
    )
    
    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    
    # Force the LLM to output structured JSON matching RouteSchema
    router_llm = llm.with_structured_output(RouteSchema)
    
    try:
        decision = await asyncio.wait_for(
            router_llm.ainvoke(messages),
            timeout=10.0
        )
        next_step = decision.next
        
        # If the Supervisor decides to FINISH immediately but there is no AI response in the state,
        # we ask the LLM to generate a direct conversational answer.
        from langchain_core.messages import HumanMessage
        if next_step == "FINISH" and isinstance(state["messages"][-1], HumanMessage):
            conversational_response = await asyncio.wait_for(
                llm.ainvoke(messages),
                timeout=15.0
            )
            return {"next": "FINISH", "messages": [conversational_response]}
            
        return {"next": next_step}
    except Exception as e:
        from langchain_core.messages import AIMessage
        print(f"LLM Parsing failed: {e}")
        error_msg = AIMessage(content="My AI brain is currently offline (API Error). Please check my API Key.")
        return {"next": "FINISH", "messages": [error_msg]}


# ==========================================
# 4. Graph Construction
# ==========================================

workflow = StateGraph(GraphState)

workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Discovery", discovery_node)
workflow.add_node("Eligibility", eligibility_node)

workflow.add_edge(START, "Supervisor")

# The Supervisor routes dynamically based on the 'next' key in state
workflow.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Discovery": "Discovery",
        "Eligibility": "Eligibility",
        "FINISH": END
    }
)

# Workers always report back to the Supervisor
workflow.add_edge("Discovery", "Supervisor")
workflow.add_edge("Eligibility", "Supervisor")

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
    """Entry point for the FastAPI route. Wraps the LangGraph execution."""
    state.messages.append(message)
    
    # Reconstruct message history for LangGraph (mocking previous turns for simplicity)
    graph_messages = [HumanMessage(content=msg) for msg in state.messages[-5:]] # Keep some history
    initial_graph_state = {
        "messages": graph_messages, 
        "next": "", 
        "skills": state.skills,
        "target_role": state.target_role,
        "location": state.location,
        "opportunities": state.opportunities
    }
    
    try:
        # Execute the graph with an outer timeout
        result = await asyncio.wait_for(
            app.ainvoke(initial_graph_state),
            timeout=40.0
        )
        # The final response is the last message in the state
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
