"""State definition for LangGraph intelligence pipeline."""

from typing import TypedDict, Optional, List, Dict, Any
from nexuspulse.ingestion.models import RawArticle, ProcessedIntel


class IntelligenceState(TypedDict):
    """Execution state passed through the LangGraph intelligence pipeline."""

    article: RawArticle
    triage_score: float
    triage_reasoning: str
    is_promising: bool

    scout_entities: List[str]
    scout_context: str

    draft_report: Optional[Dict[str, Any]]
    critic_passed: bool
    critic_feedback: str
    critic_score: float

    attempts: int
    final_intel: Optional[ProcessedIntel]
