"""Semantic chunker for structured intelligence reports."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from nexuspulse.ingestion.models import ProcessedIntel


class DocumentChunk(BaseModel):
    """Chunk of an intelligence report indexed for retrieval."""

    chunk_id: str
    report_id: str
    title: str
    section: str
    content: str
    published_at: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SemanticChunker:
    """Splits processed intelligence into semantic sections."""

    @staticmethod
    def chunk_intel(intel: ProcessedIntel) -> List[DocumentChunk]:
        """Decompose structured report into distinct retrievable sections."""
        chunks = []

        # 1. Executive Summary Chunk
        chunks.append(
            DocumentChunk(
                chunk_id=f"{intel.id}_summary",
                report_id=intel.id,
                title=intel.title,
                section="Summary & Background",
                content=f"【摘要】{intel.summary}\n【技术背景】{intel.background}",
                published_at=intel.published_at,
                metadata={"source": intel.source_name, "url": intel.source_url, "tags": intel.tags},
            )
        )

        # 2. Breakthroughs Chunk
        breakthroughs_text = "\n".join([f"- {b}" for b in intel.core_breakthroughs])
        chunks.append(
            DocumentChunk(
                chunk_id=f"{intel.id}_breakthroughs",
                report_id=intel.id,
                title=intel.title,
                section="Core Breakthroughs",
                content=f"【核心技术突破】\n{breakthroughs_text}",
                published_at=intel.published_at,
                metadata={"entities": intel.key_entities, "triage_score": intel.triage_score},
            )
        )

        # 3. Pitfalls & Impact Chunk
        pitfalls_text = "\n".join([f"- {p}" for p in intel.technical_pitfalls])
        chunks.append(
            DocumentChunk(
                chunk_id=f"{intel.id}_pitfalls",
                report_id=intel.id,
                title=intel.title,
                section="Technical Pitfalls & Engineering Impact",
                content=f"【落地风险与隐患】\n{pitfalls_text}\n【工程指导】{intel.engineering_impact}",
                published_at=intel.published_at,
                metadata={"critic_verdict": intel.critic_verdict},
            )
        )

        return chunks
