"""FastMCP Server providing standard IDE endpoints for Cursor & Claude Code."""

from typing import Optional
from fastmcp import FastMCP
from nexuspulse.rag.vector_store import InMemoryVectorStore
from nexuspulse.config import settings

# Global in-memory store for server lifetime
global_store = InMemoryVectorStore()


def create_mcp_server(store: Optional[InMemoryVectorStore] = None) -> FastMCP:
    """Create and configure the FastMCP server instance."""
    active_store = store or global_store
    mcp = FastMCP("NexusPulse-Knowledge-Brain")

    @mcp.tool()
    def search_tech_intel(query: str, top_k: int = 3) -> str:
        """Search curated tech intelligence using time-decayed hybrid retrieval.

        Args:
            query: The technical topic, framework, or bug pattern to look up.
            top_k: Number of ranked chunks to return.
        """
        results = active_store.search_hybrid(query, top_k=top_k)
        if not results:
            return f"知识中枢中暂未检索到与 '{query}' 匹配的高信噪比技术研报。"

        lines = [f"### 🪐 NexusPulse 知识中枢召回结果 (共 {len(results)} 条)"]
        for i, r in enumerate(results, 1):
            lines.append(
                f"\n#### [{i}] {r.title} ({r.section})\n"
                f"- **综合得分**: `{r.hybrid_score}` (向量分: {r.dense_score}, 稀疏分: {r.sparse_score}, 时间衰减: {r.time_decay})\n"
                f"- **详情内容**:\n{r.content}\n"
            )
        return "\n".join(lines)

    @mcp.tool()
    def get_system_status() -> str:
        """Check the status of NexusPulse intelligence database and services."""
        chunk_count = len(active_store.chunks)
        return (
            f"**NexusPulse Intelligence Engine Status**:\n"
            f"- 已索引文档切片数: `{chunk_count}`\n"
            f"- 检索模型架构: `Dense(HNSW) + Sparse(BM25) + Newton Time-Decay`\n"
            f"- 默认半衰期 Lambda: `{settings.time_decay_lambda}`\n"
            f"- 模型端点: `{settings.llm_provider}` (`{settings.llm_model}`)\n"
        )

    return mcp


if __name__ == "__main__":
    server = create_mcp_server()
    server.run()
