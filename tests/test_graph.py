"""Tests for LangGraph multi-agent review graph and critic loop."""

import pytest
from datetime import datetime, timezone
from nexuspulse.ingestion.models import RawArticle
from nexuspulse.agents.graph import run_intelligence_pipeline


@pytest.mark.asyncio
async def test_low_quality_article_filtered_at_triage():
    """Verify that marketing/clickbait article is dropped at Triage node."""
    clickbait = RawArticle(
        id="test-clickbait",
        title="Shocking! Replace all engineers with this 10 line script!",
        url="https://example.com/clickbait",
        content="Buy our masterclass to learn this 10 lines script that will replace developers!",
        source_name="SpamFeed",
        published_at=datetime.now(timezone.utc),
    )

    intel = await run_intelligence_pipeline(clickbait)
    # Must be dropped before producing final report
    assert intel is None


@pytest.mark.asyncio
async def test_high_quality_article_passes_critic_loop():
    """Verify that architecture articles enter the state graph and pass critic review."""
    tech_article = RawArticle(
        id="test-high-tech",
        title="LangGraph v0.2 Release: Durable State Machine and Checkpointing",
        url="https://example.com/langgraph",
        content="Benchmark shows durable execution prevents lost state across multi-step LLM chains.",
        source_name="TechBlog",
        published_at=datetime.now(timezone.utc),
    )

    intel = await run_intelligence_pipeline(tech_article)
    assert intel is not None
    assert intel.triage_score >= 7.0
    # In mock simulation, attempt 1 was criticized and attempt 2 passed
    assert intel.critic_attempts >= 1
    assert intel.critic_verdict in ("Approved", "Passed", "Forced_Pass_Max_Attempts")
    assert len(intel.core_breakthroughs) > 0
    assert len(intel.technical_pitfalls) > 0
