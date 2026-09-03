"""LangGraph topology compilation and pipeline executor."""

import logging
from typing import Optional
from langgraph.graph import StateGraph, END

from nexuspulse.agents.state import IntelligenceState
from nexuspulse.agents.nodes import triage_node, scout_node, synthesis_node, critic_node
from nexuspulse.ingestion.models import RawArticle, ProcessedIntel
from nexuspulse.config import settings

logger = logging.getLogger(__name__)


def route_after_triage(state: IntelligenceState) -> str:
    """Route based on triage score."""
    if state.get("is_promising", False):
        return "scout"
    return END


def route_after_critic(state: IntelligenceState) -> str:
    """Route after critic evaluation: continue loop or finalize."""
    passed = state.get("critic_passed", False)
    attempts = state.get("attempts", 1)
    if passed or attempts >= settings.max_critic_attempts:
        return END
    return "synthesis"


def build_intelligence_graph():
    """Build and compile the LangGraph multi-agent review state machine."""
    workflow = StateGraph(IntelligenceState)

    # 1. Add nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("scout", scout_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("critic", critic_node)

    # 2. Add control flow edges
    workflow.set_entry_point("triage")
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {"scout": "scout", END: END},
    )
    workflow.add_edge("scout", "synthesis")
    workflow.add_edge("synthesis", "critic")
    workflow.add_conditional_edges(
        "critic",
        route_after_critic,
        {"synthesis": "synthesis", END: END},
    )

    return workflow.compile()


async def run_intelligence_pipeline(article: RawArticle) -> Optional[ProcessedIntel]:
    """Execute the full agent workflow for an article."""
    app = build_intelligence_graph()
    initial_state: IntelligenceState = {
        "article": article,
        "triage_score": 0.0,
        "triage_reasoning": "",
        "is_promising": False,
        "scout_entities": [],
        "scout_context": "",
        "draft_report": None,
        "critic_passed": False,
        "critic_feedback": "",
        "critic_score": 0.0,
        "attempts": 0,
        "final_intel": None,
    }

    final_state = await app.ainvoke(initial_state)
    return final_state.get("final_intel")
