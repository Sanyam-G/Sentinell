import json
import os
import subprocess
from pathlib import Path
from textwrap import dedent

from langchain_anthropic import ChatAnthropic

from services.git_manager import repo_manager
from state import SREState


def act(state: SREState) -> SREState:
    """Execute the remediation plan by running commands and fixing code."""
    if not state.plan:
        state.add_step("No plan available; cannot execute")
        return state

    if not state.repo:
        state.add_step("No repo context; skipping execution")
        return state

    try:
        checkout = repo_manager.ensure_checkout(state.repo)
        state.add_step(f"Working in {checkout}")

        # Execute safe commands (pytest, linting, etc.)
        for command in state.plan.commands:
            if _is_safe_command(command):
                _run_command(command, checkout, state)
            else:
                state.add_step(f"Skipped unsafe command: {command}")

        # Fix files using LLM
        if state.plan.files_to_touch:
            _fix_files_with_llm(checkout, state)

        # Don't commit here - let PR service handle the commit
        # Just leave the fixed files in the working directory

        state.add_step("Remediation executed")
    except Exception as exc:
        state.add_step(f"Execution failed: {exc}")

    return state


def _is_safe_command(cmd: str) -> bool:
    """Only allow read-only and test commands."""
    safe_prefixes = [
        "pytest",
        "python -m pytest",
        "python -c",
        "pip install",
        "python -m py_compile",
        "find",
        "cat",
        "ls",
        "grep",
    ]
    return any(cmd.startswith(prefix) for prefix in safe_prefixes)


def _run_command(cmd: str, cwd: Path, state: SREState) -> None:
    """Run a shell command and log output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            state.add_step(f"✓ {cmd}")
        else:
            state.add_step(f"✗ {cmd} (exit {result.returncode})")
            if result.stderr:
                state.add_step(f"Error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        state.add_step(f"✗ {cmd} (timeout)")
    except Exception as exc:
        state.add_step(f"✗ {cmd} ({exc})")


def _fix_files_with_llm(checkout: Path, state: SREState) -> None:
    """Use LLM to detect and fix syntax/lint errors in target files."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        state.add_step("Skipping file fixes (no ANTHROPIC_API_KEY)")
        return

    llm = ChatAnthropic(model="claude-sonnet-4-20250514")

    for file_path in state.plan.files_to_touch:
        full_path = checkout / file_path
        if not full_path.exists() or full_path.is_dir():
            continue

        try:
            original = full_path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Ask LLM to fix the file
        prompt = dedent(
            f"""
            Fix any syntax errors, import issues, or obvious bugs in this file.
            Return ONLY the corrected file content, no explanations.

            File: {file_path}
            ---
            {original}
            ---

            Corrected file:
            """
        ).strip()

        try:
            response = llm.invoke(prompt)
            fixed = response.content.strip()

            # Remove markdown code fences if present
            if fixed.startswith("```"):
                lines = fixed.split("\n")
                fixed = "\n".join(lines[1:-1]) if len(lines) > 2 else fixed

            # Only write if content changed
            if fixed != original and len(fixed) > 10:
                full_path.write_text(fixed, encoding="utf-8")
                state.add_step(f"✓ Fixed {file_path}")
            else:
                state.add_step(f"○ No changes needed for {file_path}")
        except Exception as exc:
            state.add_step(f"✗ Failed to fix {file_path}: {exc}")


def _commit_fixes(checkout: Path, state: SREState) -> None:
    """Commit any file changes made during remediation."""
    try:
        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=checkout,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Configure git
            subprocess.run(["git", "config", "user.name", "Sentinell Bot"], cwd=checkout)
            subprocess.run(["git", "config", "user.email", "bot@sentinell.local"], cwd=checkout)
            
            # Stage and commit
            subprocess.run(["git", "add", "-A"], cwd=checkout)
            subprocess.run(
                ["git", "commit", "-m", f"Fix: {state.incident.title if state.incident else 'Auto-remediation'}"],
                cwd=checkout,
            )
            state.add_step("✓ Committed fixes locally")
    except Exception as exc:
        state.add_step(f"✗ Failed to commit fixes: {exc}")
