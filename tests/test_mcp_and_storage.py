"""Tests for vector store chunking, hybrid retrieval, and FastMCP endpoints."""

from datetime import datetime, timezone
from nexuspulse.ingestion.models import ProcessedIntel
from nexuspulse.rag.chunker import SemanticChunker
from nexuspulse.rag.vector_store import InMemoryVectorStore
from nexuspulse.distribution.mcp_server import create_mcp_server


def test_chunking_and_hybrid_search():
    sample_intel = ProcessedIntel(
        id="intel-101",
        title="PostgreSQL 16 and pgvector HNSW Indexing",
        source_url="https://example.com/pgvector",
        source_name="PostgresNews",
        triage_score=8.8,
        summary="HNSW index enables sub-millisecond approximate nearest neighbor search.",
        background="Vector embeddings require specialized index structures.",
        core_breakthroughs=["Parallel index build", "FP16 halfvec quantization"],
        technical_pitfalls=["RAM memory overhead under large collections"],
        engineering_impact="Recommended for production vector RAG workloads.",
        key_entities=["pgvector", "PostgreSQL", "HNSW"],
        tags=["Database", "Vector"],
        published_at=datetime.now(timezone.utc),
    )

    chunks = SemanticChunker.chunk_intel(sample_intel)
    assert len(chunks) == 3

    store = InMemoryVectorStore()
    store.add_chunks(chunks)

    # Search for "pgvector HNSW"
    results = store.search_hybrid("pgvector HNSW", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "pgvector" in top_result.content or "HNSW" in top_result.content
    assert top_result.hybrid_score > 0.0


def test_mcp_server_tools():
    store = InMemoryVectorStore()
    server = create_mcp_server(store=store)
    assert server.name == "NexusPulse-Knowledge-Brain"
