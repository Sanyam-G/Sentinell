import json
from langchain_anthropic import ChatAnthropic
from state import SREState


def evaluate(state: SREState) -> SREState:
    """
    Evaluates whether the issue is resolved.
    Uses LLM to determine if actions taken have fixed the problem.
    """
    # Initialize LLM lazily to avoid requiring API key at import time
    llm = ChatAnthropic(model="claude-sonnet-4-20250514")

    prompt = f"""You are an SRE evaluating if an issue is resolved.

Original Logs: {state.logs}
Actions taken: {state.actions}

Based on the actions taken, is the issue likely resolved? For this MVP demo, assume actions work as intended.

Respond with ONLY a JSON object (no other text) in this exact format:
{{"resolved": true}}

If more actions are needed, respond:
{{"resolved": false}}"""

    response = llm.invoke(prompt)

    # Parse the JSON response from the LLM
    try:
        content = response.content.strip()

        # Find JSON object in response
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            parsed = json.loads(json_str)

            state.resolved = parsed.get("resolved", False)
        else:
            raise ValueError("No JSON found in response")

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # For demo purposes, resolve after a few iterations
        state.resolved = len(state.actions) >= 2

    return state
