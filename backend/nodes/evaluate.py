from datetime import datetime

from state import SREState


def evaluate(state: SREState) -> SREState:
    """Mark the incident as resolved once a plan has been executed."""
    if state.incident is None:
        state.add_step("No incident; evaluation complete")
        state.resolved = True
        return state

    if state.plan is None:
        state.add_step("Evaluation pending: no plan yet")
        state.resolved = False
    else:
        state.add_step("Plan ready for PR creation; marking resolved")
        state.resolved = True
        if state.incident:
            state.incident.metadata["resolved_at"] = datetime.utcnow().isoformat()
    return state
