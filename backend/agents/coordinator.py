"""The Dynamic LangGraph Supervisor (Advanced Multi-Agent Orchestration)."""

from __future__ import annotations

import uuid
import operator
from dataclasses import asdict, dataclass, field
from typing import Literal, TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from backend.services.resume_ingestion import get_llm
from backend.tools.search import search_duckduckgo, search_adzuna


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

class GraphState(TypedDict):
    """The internal LangGraph state passed between nodes."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str
    skills: list[str]


# ==========================================
# 2. Worker Agents (Deterministic Nodes)
# ==========================================

def discovery_node(state: GraphState):
    """Executes the Discovery Agent in a fixed, deterministic pipeline."""
    llm = get_llm()
    skills = state.get("skills", [])
    
    # 1. Deterministic Search Execution
    query = f"{' '.join(skills[:3])} internship opportunities" if skills else "software engineering internships"
    
    try:
        # Call the search tool explicitly without agent looping
        raw_results = search_duckduckgo.invoke({"query": query})
    except Exception as e:
        raw_results = f"Search failed: {e}"
        
    # 2. Synthesis (LLM Call)
    skills_context = f"The user has the following skills: {', '.join(skills)}." if skills else ""
    prompt = (
        f"You are the Discovery Agent. {skills_context}\n"
        f"I searched the web for '{query}' and found these raw results:\n\n{raw_results}\n\n"
        "Synthesize these findings into a beautifully formatted list of 2-3 internship opportunities. "
        "Highlight why they are a good match for the user's skills."
    )
    
    from langchain_core.messages import SystemMessage
    response = llm.invoke([SystemMessage(content=prompt)] + list(state["messages"]))
    
    return {"messages": [response]}


def eligibility_node(state: GraphState):
    """Executes the Eligibility Agent in a fixed, deterministic pipeline."""
    llm = get_llm()
    skills = state.get("skills", [])
    skills_context = f"The user has the following skills: {', '.join(skills)}." if skills else ""
    
    prompt = (
        f"You are the Eligibility Agent. {skills_context}\n"
        "Your responsibility is to evaluate if the candidate is a good fit "
        "for the jobs currently discussed in the conversation. Be highly analytical. Highlight missing skills."
    )
    
    from langchain_core.messages import SystemMessage
    response = llm.invoke([SystemMessage(content=prompt)] + list(state["messages"]))
    return {"messages": [response]}


class RouteSchema(BaseModel):
    """Schema forcing the LLM to output a strict routing decision."""
    next: Literal["Discovery", "Eligibility", "FINISH"] = Field(
        description="The next worker to route to. Use FINISH if the user's request has been fully addressed."
    )


def supervisor_node(state: GraphState):
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
        decision = router_llm.invoke(messages)
        next_step = decision.next
        
        # If the Supervisor decides to FINISH immediately but there is no AI response in the state,
        # we ask the LLM to generate a direct conversational answer.
        from langchain_core.messages import HumanMessage
        if next_step == "FINISH" and isinstance(state["messages"][-1], HumanMessage):
            conversational_response = llm.invoke(messages)
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


def new_state(session_id: str | None = None) -> ConversationState:
    return ConversationState(session_id=session_id or str(uuid.uuid4()), trace_id=str(uuid.uuid4()))


def coordinate(message: str, state: ConversationState) -> CoordinatorResult:
    """Entry point for the FastAPI route. Wraps the LangGraph execution."""
    state.messages.append(message)
    
    # Reconstruct message history for LangGraph (mocking previous turns for simplicity)
    graph_messages = [HumanMessage(content=message)]
    initial_graph_state = {"messages": graph_messages, "next": "", "skills": state.skills}
    
    try:
        # Execute the graph
        result = app.invoke(initial_graph_state)
        # The final response is the last message in the state
        final_message = result["messages"][-1].content
        action = result.get("next", "FINISH")
    except Exception as e:
        print(f"Graph Error: {e}")
        final_message = "I encountered an error while orchestrating the agents. Please try again."
        action = "error"
        
    return CoordinatorResult(
        state=state,
        action=action,
        response=final_message,
        missing_fields=[],
    )


def serialize_state(state: ConversationState) -> dict:
    return asdict(state)


def deserialize_state(payload: dict) -> ConversationState:
    return ConversationState(**payload)
