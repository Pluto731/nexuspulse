"""Tests for content deduplication."""

from nexuspulse.ingestion.dedupe import ContentDeduplicator


def test_exact_hash_deduplication():
    deduper = ContentDeduplicator()
    title = "LangGraph 0.2 Announcement"
    content = "LangGraph v0.2 has been released with durable state persistence."

    assert not deduper.is_duplicate(title, content)
    deduper.register("item-1", title, content)

    # Exact content match must be flagged duplicate
    assert deduper.is_duplicate("Different Title Same Content", content)
    assert deduper.is_duplicate("Different Title", "  LangGraph v0.2 has been released with durable state persistence.  ")


def test_near_duplicate_title_detection():
    deduper = ContentDeduplicator(sim_threshold=0.8)
    title = "Release: LangGraph v0.2 Durable State Machine"
    content = "First article body about LangGraph."

    deduper.register("item-1", title, content)

    # Highly overlapping title with different body
    similar_title = "Release LangGraph v0.2 Durable State Machine Feature"
    assert deduper.is_duplicate(similar_title, "Completely different article text")

    # Distinct title
    unrelated_title = "Postgres pgvector Performance Benchmark in 2026"
    assert not deduper.is_duplicate(unrelated_title, "Completely different article text")
