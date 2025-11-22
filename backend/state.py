from pydantic import BaseModel
from typing import Optional, List


class SREState(BaseModel):
    logs: Optional[str] = None
    issue: Optional[str] = None
    actions: List[str] = []
    resolved: bool = False
