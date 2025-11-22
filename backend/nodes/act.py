from state import SREState


def act(state: SREState) -> SREState:
    """
    Executes the proposed action.
    In this MVP, we just print the action.
    Replace with real kubectl/aws/docker/etc. commands later.
    """
    if state.actions:
        action = state.actions[-1]
        print(f"[ACTION] {action}")

    return state
