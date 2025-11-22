import json
from langchain_openai import ChatOpenAI
from state import SREState


def evaluate(state: SREState) -> SREState:
    """
    Evaluates whether the issue is resolved.
    Uses LLM to determine if actions taken have fixed the problem.
    """
    # Initialize LLM lazily to avoid requiring API key at import time
    llm = ChatOpenAI(model="gpt-4o-mini")

    prompt = f"""
    Logs: {state.logs}
    Actions taken: {state.actions}
    Is the issue resolved?
    Respond JSON: {{ "resolved": true/false }}
    """

    response = llm.invoke(prompt)

    # Parse the JSON response from the LLM
    try:
        parsed = json.loads(response.content)
        state.resolved = parsed["resolved"]
    except (json.JSONDecodeError, KeyError) as e:
        # Default to False if we can't parse the response
        state.resolved = False

    return state
