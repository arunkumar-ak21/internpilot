"""Opportunity Discovery Agent."""

from backend.agents.coordinator import ConversationState

def run_discovery_agent(state: ConversationState) -> str:
    """Mock implementation of the Discovery Agent."""
    role = state.target_role or "roles"
    location = state.location or "locations"
    
    # In a real implementation, this would call the OpportunityProvider
    # and use an LLM to filter/sort the results.
    
    return f"I have searched for {role} opportunities in {location}. Found a few promising leads!"
