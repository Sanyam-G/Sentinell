"""
State definition for the code-fixing agent.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class AgentState(BaseModel):
    """State that flows through the agent graph."""
    
    # Input
    input_text: Optional[str] = None  # Slack message or log entry
    input_type: Optional[str] = None  # "slack", "log", or "manual"
    
    # Issue detection
    detected_issue: Optional[str] = None
    issue_confidence: Optional[float] = None
    
    # Context from Pinecone
    relevant_commits: List[Dict[str, Any]] = []
    relevant_logs: List[Dict[str, Any]] = []
    relevant_slack: List[Dict[str, Any]] = []
    
    # Code analysis
    affected_files: List[str] = []
    code_context: Optional[str] = None
    root_cause: Optional[str] = None
    
    # Solution
    proposed_fix: Optional[str] = None
    code_changes: Dict[str, Any] = {}  # file_path -> {"old": "...", "new": "..."} or just new content
    
    # PR creation
    pr_created: bool = False
    pr_url: Optional[str] = None
    pr_branch: Optional[str] = None
    
    # Status
    status: str = "initialized"  # initialized, detecting, analyzing, fixing, creating_pr, done
    error: Optional[str] = None

