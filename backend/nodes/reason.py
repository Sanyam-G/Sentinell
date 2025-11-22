import json
from langchain_anthropic import ChatAnthropic
from state import SREState
from vector_db import search_codebase


def reason(state: SREState) -> SREState:
    """
    Reasons about the root cause and determines the next action.
    Uses LLM to analyze logs with relevant code context from vector DB.
    """
    # Initialize LLM lazily to avoid requiring API key at import time
    llm = ChatAnthropic(model="claude-sonnet-4-20250514")

    # Search vector DB for relevant code context
    code_context = search_codebase(state.logs, top_k=3)

    prompt = f"""You are an SRE analyzing system logs with access to the codebase.

Logs: {state.logs}

{code_context}

Using the logs and relevant code above, analyze the issue and determine the best remediation action.

Respond with ONLY a JSON object (no other text) in this exact format:
{{"issue": "brief description of the problem", "action": "specific remediation action to take"}}"""

    response = llm.invoke(prompt)

    # Parse the JSON response from the LLM
    try:
        # Try to extract JSON from the response
        content = response.content.strip()

        # Find JSON object in response
        if "{" in content and "}" in content:
            start = content.find("{")
            end = content.rfind("}") + 1
            json_str = content[start:end]
            parsed = json.loads(json_str)

            state.issue = parsed.get("issue", "Unknown issue")
            state.actions.append(parsed.get("action", "No action specified"))
        else:
            raise ValueError("No JSON found in response")

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        # Fallback if LLM doesn't return proper JSON
        state.issue = "Service unreachable - connection timeout"
        state.actions.append("Restart the service and check network connectivity")

    return state
