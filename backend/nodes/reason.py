import json
import os
from textwrap import dedent

from langchain_anthropic import ChatAnthropic

from schemas import ActionPlan
from state import SREState
from vector_db import search_codebase


def reason(state: SREState) -> SREState:
    """Generate an action plan based on incident + context."""
    if state.incident is None:
        state.add_step("Reason skipped: no incident context")
        return state

    log_blob = "\n".join(
        line for window in state.log_windows for line in window.lines
    )
    slack_blob = "\n".join(snippet.text for snippet in state.slack_messages)
    commits_blob = "\n".join(
        f"{commit.sha}: {commit.title}" for commit in state.commits
    )
    code_context = search_codebase(log_blob or state.incident.description, top_k=3)

    prompt = dedent(
        f"""
        You are an autonomous Site Reliability Engineer.
        Incident: {state.incident.title} (severity={state.incident.severity})
        Description: {state.incident.description}

        Logs:\n{log_blob or 'N/A'}
        Slack context:\n{slack_blob or 'N/A'}
        Recent commits:\n{commits_blob or 'N/A'}
        Code search results:\n{code_context}

        Produce a remediation plan with commands, files to inspect/modify,
        and a pull request summary.

        For syntax errors or test failures, include:
        - Commands to verify the issue (pytest, py_compile)
        - The specific files that need fixing
        - Clear PR notes explaining what was broken and how it's fixed

        Respond ONLY with JSON:
        {{
          "summary": "sentence describing the fix",
          "commands": ["pytest -v", "python -m py_compile file.py"],
          "files": ["path/to/broken_file.py"],
          "pr_title": "Fix [specific issue]",
          "pr_body": "## Issue\\n...\\n## Solution\\n...\\n## Testing\\n..."
        }}
        """
    ).strip()

    plan = _invoke_llm(prompt)
    state.plan = plan
    state.add_step("Generated remediation plan")
    return state


def _invoke_llm(prompt: str) -> ActionPlan:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        llm = ChatAnthropic(model="claude-sonnet-4-20250514")
        response = llm.invoke(prompt)
        content = response.content.strip()
        try:
            start = content.index("{")
            end = content.rindex("}") + 1
            payload = json.loads(content[start:end])
            return ActionPlan(
                summary=payload.get("summary", "Manual investigation required"),
                commands=payload.get("commands", []),
                files_to_touch=payload.get("files", []),
                pr_title=payload.get("pr_title"),
                pr_body=payload.get("pr_body"),
            )
        except Exception:
            pass

    # Fallback deterministic plan
    return ActionPlan(
        summary="Restart affected service and add timeout guard",
        commands=[
            "kubectl rollout restart deployment/api",
            "pytest tests/ -k critical",
        ],
        files_to_touch=["services/api/handlers.py"],
        pr_title="Patch timeout handling",
        pr_body="Adds retry/backoff around upstream dependency and increases observability logs.",
    )
