"""Vector store implementation with hybrid retrieval and in-memory mock."""

import re
import numpy as np
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone

from nexuspulse.rag.chunker import DocumentChunk
from nexuspulse.rag.decay import hybrid_score
from nexuspulse.config import settings


class SearchResult(BaseModel):
    """Ranked retrieval result."""

    chunk_id: str
    report_id: str
    title: str
    section: str
    content: str
    dense_score: float
    sparse_score: float
    time_decay: float
    hybrid_score: float
    metadata: Dict[str, Any]


class InMemoryVectorStore:
    """Zero-dependency in-memory vector store for testing and rapid local prototype execution."""

    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.chunks: Dict[str, DocumentChunk] = {}
        self.vectors: Dict[str, np.ndarray] = {}

    def _pseudo_embed(self, text: str) -> np.ndarray:
        """Deterministic pseudo-embedding for zero-dependency offline prototyping."""
        np.random.seed(abs(hash(text)) % (2**31))
        vec = np.random.randn(self.dimension).astype(np.float32)
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    @staticmethod
    def _token_similarity(query: str, text: str) -> float:
        """Keyword matching score simulating sparse BM25 / pg_trgm similarity."""
        q_tokens = set(re.findall(r"\w+", query.lower()))
        t_tokens = set(re.findall(r"\w+", text.lower()))
        if not q_tokens or not t_tokens:
            return 0.0
        overlap = len(q_tokens & t_tokens)
        return min(1.0, overlap / (len(q_tokens) ** 0.5))

    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add chunks and compute simulated vectors."""
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            self.vectors[chunk.chunk_id] = self._pseudo_embed(chunk.content)

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        alpha: Optional[float] = None,
        reference_time: Optional[datetime] = None,
    ) -> List[SearchResult]:
        """Perform hybrid search with time decay."""
        if alpha is None:
            alpha = settings.dense_weight
        if reference_time is None:
            reference_time = datetime.now(timezone.utc)

        q_vec = self._pseudo_embed(query)
        scored_results = []

        for chunk_id, chunk in self.chunks.items():
            doc_vec = self.vectors[chunk_id]
            dense_sim = float(np.dot(q_vec, doc_vec))
            # Rescale cosine [-1, 1] to [0, 1]
            dense_norm = max(0.0, (dense_sim + 1.0) / 2.0)

            sparse_sim = self._token_similarity(query, f"{chunk.title} {chunk.content}")

            final_score = hybrid_score(
                dense_sim=dense_norm,
                sparse_sim=sparse_sim,
                published_at=chunk.published_at,
                alpha=alpha,
                decay_lambda=settings.time_decay_lambda,
                reference_time=reference_time,
            )

            # Calculate individual decay component for transparency
            from nexuspulse.rag.decay import compute_time_decay
            decay_factor = compute_time_decay(chunk.published_at, reference_time, settings.time_decay_lambda)

            scored_results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    report_id=chunk.report_id,
                    title=chunk.title,
                    section=chunk.section,
                    content=chunk.content,
                    dense_score=round(dense_norm, 4),
                    sparse_score=round(sparse_sim, 4),
                    time_decay=round(decay_factor, 4),
                    hybrid_score=round(final_score, 4),
                    metadata=chunk.metadata,
                )
            )

        scored_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        return scored_results[:top_k]

    @staticmethod
    def get_pgvector_sql_template() -> str:
        """Returns the PostgreSQL pgvector + pg_trgm SQL used in production deployment."""
        return """
        SELECT 
            c.id, c.content, c.metadata,
            (
                :alpha * (1 - (c.embedding <=> :query_vector)) +
                (1 - :alpha) * similarity(c.content, :query_text)
            ) * EXP(-:decay_lambda * (EXTRACT(EPOCH FROM (NOW() - c.created_at)) / 3600)) AS hybrid_score
        FROM document_chunks c
        WHERE (c.embedding <=> :query_vector) < 0.5 OR similarity(c.content, :query_text) > 0.15
        ORDER BY hybrid_score DESC
        LIMIT :top_k;
        """
