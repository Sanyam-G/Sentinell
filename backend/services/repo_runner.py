"""Utilities for cloning repos and running their self-check scripts."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from schemas import RepoPollResult, RepoSnapshot
from services.git_manager import repo_manager

DEFAULT_CHECK_SCRIPT = os.getenv("SRE_CHECK_SCRIPT", "scripts/run_checks.sh")

logger = logging.getLogger(__name__)


def _install_requirements(checkout_path: Path) -> None:
    """Install repo-specific requirements so tests do not fail on missing deps."""
    for filename in ("requirements.txt", "requirements-dev.txt"):
        req_file = checkout_path / filename
        if not req_file.exists():
            continue

        logger.info("Installing dependencies from %s", req_file)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req_file.as_posix()],
            cwd=checkout_path,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            logger.error("pip install failed for %s: %s", req_file, result.stderr.strip())
            raise RuntimeError(
                f"Failed to install dependencies for {checkout_path.name}: {req_file.name}"
            )

        logger.debug("pip install output: %s", result.stdout.strip())
        break

    # Ensure greenlet is installed for SQLAlchemy asyncio support
    # This is often missed in requirements but required by the runner environment
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "greenlet"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        logger.warning("Failed to force install greenlet; tests may fail if using asyncio")


class RepoRunner:
    def __init__(self, relative_script: str = DEFAULT_CHECK_SCRIPT) -> None:
        self.relative_script = Path(relative_script)

    def run_checks(self, repo: RepoSnapshot) -> RepoPollResult:
        checkout_path = repo_manager.ensure_checkout(repo)
        
        # Install dependencies using the backend's Python interpreter
        _install_requirements(checkout_path)

        # Instead of running the repo's script (which may use wrong Python),
        # run pytest directly using the backend's Python interpreter
        # This guarantees we use the correct environment with greenlet installed
        tests_dir = checkout_path / "tests"
        
        if not tests_dir.exists():
            raise FileNotFoundError(
                f"Expected tests directory at {tests_dir}, but it does not exist"
            )

        logger.info("Running tests using backend Python interpreter: %s", sys.executable)
        
        # Create a clean environment to prevent system site-packages from leaking in
        env = os.environ.copy()
        # Force pytest to use ONLY the venv site-packages, not system or conda packages
        env["PYTHONNOUSERSITE"] = "1"
        # Unset any PYTHONPATH that might cause issues
        env.pop("PYTHONPATH", None)
        
        result = subprocess.run(
            [sys.executable, "-m", "pytest", tests_dir.as_posix(), "-q", "--disable-warnings", "--maxfail=1"],
            cwd=checkout_path,
            text=True,
            capture_output=True,
            env=env,
        )

        return RepoPollResult(
            repo_id=repo.id,
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            ran_at=datetime.utcnow(),
        )


def _get_runner() -> RepoRunner:
    return RepoRunner()


repo_runner = _get_runner()
