from state import SREState


def observe(state: SREState) -> SREState:
    """Acknowledge the hydrated incident context provided by the worker."""
    if state.incident is None:
        state.add_step("No incident bound to state; exiting")
        state.resolved = True
        return state

    state.add_step(f"Observing signals for incident {state.incident.id}")
    return state
