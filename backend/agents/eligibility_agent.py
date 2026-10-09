"""Eligibility Verification Agent."""

from backend.agents.coordinator import ConversationState

def run_eligibility_agent(state: ConversationState) -> str:
    """Mock implementation of the Eligibility Agent."""
    
    # In a real implementation, this would pull the student's profile,
    # compare it against the opportunity requirements, and output a detailed breakdown.
    
    return "I checked your profile against the requirements. It looks like you meet the core criteria!"
