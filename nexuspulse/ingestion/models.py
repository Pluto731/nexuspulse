"""Data models for raw articles and processed intelligence."""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class RawArticle(BaseModel):
    """Raw article fetched from an RSS, HackerNews, or ArXiv feed."""

    id: Optional[str] = None
    title: str
    url: str
    content: str
    summary: Optional[str] = None
    source_name: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessedIntel(BaseModel):
    """Refined and structured intelligence report after multi-agent critique."""

    id: str
    title: str
    source_url: str
    source_name: str
    triage_score: float
    summary: str
    background: str
    core_breakthroughs: List[str]
    technical_pitfalls: List[str]
    engineering_impact: str
    key_entities: List[str] = Field(default_factory=list)  # e.g., ["pgvector", "LangGraph"]
    tags: List[str] = Field(default_factory=list)
    published_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    critic_attempts: int = 1
    critic_verdict: str = "Passed"
