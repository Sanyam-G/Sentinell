"""SQLModel definitions for backend persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import ConfigDict
from sqlmodel import Column, DateTime, Field, JSON, SQLModel


class Repo(SQLModel, table=True):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default=None, primary_key=True)
    name: str
    repo_url: str
    default_branch: str = "main"
    github_app_installation_id: Optional[str] = None
    description: Optional[str] = None
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LogSource(SQLModel, table=True):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default=None, primary_key=True)
    name: str
    repo_id: Optional[str] = Field(default=None, foreign_key="repo.id")
    source_type: str = "loki"
    endpoint: Optional[str] = None
    auth_mode: Optional[str] = None
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SlackChannel(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    team_id: str
    channel_id: str
    channel_name: Optional[str] = None
    repo_id: Optional[str] = Field(default=None, foreign_key="repo.id")
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Incident(SQLModel, table=True):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(default=None, primary_key=True)
    signal_type: str
    title: str
    description: str
    repo_id: Optional[str] = Field(default=None, foreign_key="repo.id")
    severity: str = "medium"
    status: str = "queued"
    source_ref: Optional[str] = None
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        alias="metadata",
        sa_column=Column("metadata", JSON),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GithubEvent(SQLModel, table=True):
    id: str = Field(default=None, primary_key=True)
    delivery_id: str
    event: str
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    repo_id: Optional[str] = Field(default=None, foreign_key="repo.id")
    received_at: datetime = Field(default_factory=datetime.utcnow)
