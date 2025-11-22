import json
from langchain_openai import ChatOpenAI
from state import SREState


def reason(state: SREState) -> SREState:
    """
    Reasons about the root cause and determines the next action.
    Uses LLM to analyze logs and suggest remediation.
    """
    # Initialize LLM lazily to avoid requiring API key at import time
    llm = ChatOpenAI(model="gpt-4o-mini")

    prompt = f"""
    Logs: {state.logs}
    What is the issue and next action?
    Respond JSON: {{ "issue": "...", "action": "..." }}
    """

    response = llm.invoke(prompt)

    # Parse the JSON response from the LLM
    try:
        parsed = json.loads(response.content)
        state.issue = parsed["issue"]
        state.actions.append(parsed["action"])
    except (json.JSONDecodeError, KeyError) as e:
        # Fallback if LLM doesn't return proper JSON
        state.issue = response.content
        state.actions.append("Unable to parse action from LLM response")

    return state
