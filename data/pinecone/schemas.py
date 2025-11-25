"""Shared document schemas for Pinecone storage."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Dict, List


@dataclass
class BaseDocument:
    id: str
    repo_id: str
    timestamp: datetime
    text: str
    metadata: Dict[str, str] = field(default_factory=dict)
    source_type: ClassVar[str] = "base"


@dataclass
class LogDocument(BaseDocument):
    level: str = "info"
    source_type: ClassVar[str] = "log"


@dataclass
class SlackDocument(BaseDocument):
    channel_id: str = ""
    user: str = ""
    source_type: ClassVar[str] = "slack"


@dataclass
class CommitDocument(BaseDocument):
    sha: str = ""
    files: List[str] = field(default_factory=list)
    source_type: ClassVar[str] = "commit"
