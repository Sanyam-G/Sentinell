"""Lightweight Git operations used by the worker to clone/update repos."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

from schemas import RepoSnapshot

DEFAULT_BASE = Path(os.getenv("SRE_REPO_CACHE", "/tmp/sentinell/repos"))


class RepoManager:
    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or DEFAULT_BASE
        self.base_path.mkdir(parents=True, exist_ok=True)

    def ensure_checkout(self, repo: RepoSnapshot, preserve_changes: bool = False) -> Path:
        checkout_path = self.base_path / repo.id
        if checkout_path.exists():
            self._run_git(["fetch", "origin", repo.default_branch], cwd=checkout_path)
            if not preserve_changes:
                # Only reset if we're not preserving file changes from act node
                self._run_git(["checkout", repo.default_branch], cwd=checkout_path)
                self._run_git(["reset", "--hard", f"origin/{repo.default_branch}"], cwd=checkout_path)
            # If preserving changes, don't checkout/reset, just leave working directory as-is
        else:
            self._run_git(["clone", repo.repo_url, checkout_path.as_posix()])
            self._run_git(["checkout", repo.default_branch], cwd=checkout_path)
        return checkout_path

    def read_recent_commits(self, repo: RepoSnapshot, limit: int = 5) -> str:
        checkout_path = self.ensure_checkout(repo)
        args = [
            "log",
            f"-n{limit}",
            "--pretty=format:%h %an %ar %s",
            "--stat",
        ]
        return self._run_git(args, cwd=checkout_path)

    def _run_git(self, args: list[str], cwd: Optional[Path] = None) -> str:
        cmd = ["git", *args]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Git command failed ({' '.join(cmd)}): {result.stderr.strip()}"
            )
        return result.stdout.strip()


repo_manager = RepoManager()
