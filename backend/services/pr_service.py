"""GitHub pull-request helper used by the worker."""
from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

import requests

from schemas import ActionPlan, IncidentRecord, RepoSnapshot
from services.git_manager import repo_manager


@dataclass
class PRResult:
    url: str
    branch: str


class PullRequestService:
    """Create pull requests for repos once the agent finishes a plan."""

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN")
        self.git_user = os.getenv("SRE_GIT_USER", "Sentinell Bot")
        self.git_email = os.getenv("SRE_GIT_EMAIL", "bot@sentinell.local")

    def create_pr(self, repo: RepoSnapshot, plan: ActionPlan, *, incident: Optional[IncidentRecord] = None) -> PRResult:
        if not self.token:
            raise RuntimeError("GITHUB_TOKEN is required for PR automation")

        # Preserve changes made by act node
        checkout = repo_manager.ensure_checkout(repo, preserve_changes=True)
        self._configure_git(checkout)

        branch = self._branch_name(plan)
        
        # Check if act node made file changes (not commits, just modified files)
        has_changes = self._has_pending_changes(checkout)
        
        if not has_changes:
            # No fixes from act node, pull latest and add markdown plan
            self._git(["checkout", repo.default_branch], cwd=checkout)
            self._git(["pull", "origin", repo.default_branch], cwd=checkout)
            self._git(["checkout", "-B", branch], cwd=checkout)
            self._materialize_plan(checkout, plan, incident)
            self._git(["add", "-A"], cwd=checkout)
            
            if not self._has_pending_changes(checkout):
                return PRResult(url="", branch=repo.default_branch)
        else:
            # Act node fixed files - commit those fixes
            self._git(["checkout", "-B", branch], cwd=checkout)
            self._git(["add", "-A"], cwd=checkout)
        
        commit_message = plan.pr_title or f"Sentinell fix: {plan.summary}"
        self._git(["commit", "-m", commit_message], cwd=checkout)

        push_url = self._auth_repo_url(repo.repo_url)
        self._git(["push", push_url, branch, "--force-with-lease"], cwd=checkout)

        owner, project = self._owner_repo(repo.repo_url)
        pr_url = self._create_pull_request(
            owner,
            project,
            title=plan.pr_title or commit_message,
            head=branch,
            base=repo.default_branch,
            body=plan.pr_body or plan.summary or "Automated remediation",
        )

        return PRResult(url=pr_url, branch=branch)

    def _configure_git(self, checkout: Path) -> None:
        self._git(["config", "user.name", self.git_user], cwd=checkout)
        self._git(["config", "user.email", self.git_email], cwd=checkout)

    def _branch_name(self, plan: ActionPlan) -> str:
        base = plan.pr_title or plan.summary or "auto-fix"
        slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
        slug = slug[:32] or "auto-fix"
        return f"ai-sre/{slug}-{uuid4().hex[:6]}"

    def _has_pending_changes(self, checkout: Path) -> bool:
        status = self._git(["status", "--porcelain"], cwd=checkout)
        return bool(status.strip())

    def _has_unpushed_commits(self, checkout: Path, branch: str) -> bool:
        """Check if there are local commits not on remote."""
        try:
            result = subprocess.run(
                ["git", "rev-list", f"{branch}..origin/{branch}", "--count"],
                cwd=checkout,
                capture_output=True,
                text=True,
            )
            # If local branch is ahead, we have unpushed commits
            local_ahead = subprocess.run(
                ["git", "rev-list", f"origin/{branch}..{branch}", "--count"],
                cwd=checkout,
                capture_output=True,
                text=True,
            )
            return local_ahead.returncode == 0 and int(local_ahead.stdout.strip() or 0) > 0
        except Exception:
            return False

    def _git(self, args: list[str], cwd: Path) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout

    def _auth_repo_url(self, repo_url: str) -> str:
        parsed = urlparse(repo_url)
        netloc = f"x-access-token:{self.token}@{parsed.netloc}"
        return urlunparse(parsed._replace(netloc=netloc))

    def _owner_repo(self, repo_url: str) -> Tuple[str, str]:
        path = urlparse(repo_url).path.rstrip("/").removesuffix(".git")
        owner, _, project = path.lstrip("/").partition("/")
        if not owner or not project:
            raise ValueError(f"Unable to parse owner/repo from {repo_url}")
        return owner, project

    def _materialize_plan(
        self, checkout: Path, plan: ActionPlan, incident: Optional[IncidentRecord]
    ) -> None:
        """Write a markdown artifact so git always has concrete changes to commit."""

        notes_dir = checkout / ".sentinell"
        notes_dir.mkdir(parents=True, exist_ok=True)
        slug = incident.id if incident else uuid4().hex[:8]
        note_path = notes_dir / f"incident-{slug}.md"

        commands = "\n".join(f"- {cmd}" for cmd in plan.commands) or "- No commands suggested"
        files = "\n".join(f"- {path}" for path in plan.files_to_touch) or "- Not specified"
        plan_body = plan.pr_body or "No PR body provided"

        content = dedent(
            f"""
            # Sentinell Remediation Plan
            Incident: {incident.id if incident else 'ad-hoc'}
            Generated: {datetime.utcnow().isoformat()}Z

            ## Summary
            {plan.summary}

            ## Commands
            {commands}

            ## Files to touch
            {files}

            ## PR Notes
            {plan_body}
            """
        ).strip() + "\n"

        note_path.write_text(content, encoding="utf-8")

    def _create_pull_request(
        self,
        owner: str,
        repo: str,
        *,
        title: str,
        head: str,
        base: str,
        body: str,
    ) -> str:
        api = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        response = requests.post(
            api,
            json={"title": title, "head": head, "base": base, "body": body},
            headers={
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json",
            },
            timeout=20,
        )
        if response.status_code == 422 and "A pull request already exists" in response.text:
            # Fallback: fetch existing PR for branch
            query = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls",
                params={"head": f"{owner}:{head}"},
                headers={"Authorization": f"token {self.token}"},
                timeout=20,
            )
            query.raise_for_status()
            existing = query.json()
            if existing:
                return existing[0]["html_url"]
        response.raise_for_status()
        payload = response.json()
        return payload.get("html_url", "")


pr_service = PullRequestService()
