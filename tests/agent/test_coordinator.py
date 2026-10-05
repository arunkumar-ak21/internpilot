from backend.agents.coordinator import coordinate, new_state


def test_coordinator_clarifies_when_critical_search_information_is_missing():
    result = coordinate("I want an AI internship", new_state())
    assert result.action == "clarify"
    assert set(result.missing_fields) == {"location"}


def test_coordinator_retains_state_and_routes_complete_intent_to_search():
    state = new_state()
    coordinate("I want an AI internship", state)
    result = coordinate("in Bangalore, at least ₹15000", state)
    assert result.action == "search"
    assert result.state.target_role == "AI/ML"
    assert result.state.minimum_stipend == 15000
