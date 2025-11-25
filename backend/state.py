from typing import List, Optional

from pydantic import BaseModel, Field

from schemas import (
    ActionPlan,
    CommitSummary,
    IncidentContext,
    LogWindow,
    RepoSnapshot,
    SlackSnippet,
)


class SREState(BaseModel):
    incident: Optional[IncidentContext] = None
    repo: Optional[RepoSnapshot] = None
    repo_path: Optional[str] = None
    log_windows: List[LogWindow] = Field(default_factory=list)
    slack_messages: List[SlackSnippet] = Field(default_factory=list)
    commits: List[CommitSummary] = Field(default_factory=list)
    plan: Optional[ActionPlan] = None
    steps: List[str] = Field(default_factory=list)
    resolved: bool = False

    def add_step(self, description: str) -> "SREState":
        self.steps.append(description)
        return self
