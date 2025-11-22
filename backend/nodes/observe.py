from state import SREState


def observe(state: SREState) -> SREState:
    """
    Observes incoming signals (logs, Slack messages, etc.).
    In this MVP, we use a stubbed error log.
    Replace with real Slack/log ingestion later.
    """
    state.logs = "ERROR: service unreachable; connection timeout"
    return state
