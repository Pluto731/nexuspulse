"""LangGraph execution nodes for intelligence pipeline."""

from typing import Dict, Any
from datetime import datetime, timezone
import hashlib

from nexuspulse.agents.state import IntelligenceState
from nexuspulse.agents.llm_client import LLMClient
from nexuspulse.agents.prompts import (
    TRIAGE_SYSTEM_PROMPT,
    SCOUT_SYSTEM_PROMPT,
    SYNTHESIS_SYSTEM_PROMPT,
    CRITIC_SYSTEM_PROMPT,
)
from nexuspulse.ingestion.models import ProcessedIntel
from nexuspulse.config import settings

llm_client = LLMClient()


async def triage_node(state: IntelligenceState) -> Dict[str, Any]:
    """Node 1: Evaluates novelty and signal-to-noise ratio."""
    art = state["article"]
    user_prompt = f"标题: {art.title}\n来源: {art.source_name}\n内容摘要: {art.content[:800]}"

    # Fallback heuristic if LLM is not active
    is_clickbait = "replace" in art.title.lower() or "shocking" in art.title.lower() or "masterclass" in art.content.lower()
    mock_score = 3.2 if is_clickbait else (8.6 if "release" in art.title.lower() or "benchmark" in art.content.lower() else 7.2)
    mock_data = {
        "triage_score": mock_score,
        "reasoning": "检测到标题党与夸张营销词汇，缺乏底层工程实质" if is_clickbait else "具备扎实的架构更新与量化技术特性",
        "is_promising": mock_score >= settings.triage_threshold,
    }

    result = await llm_client.generate_json(TRIAGE_SYSTEM_PROMPT, user_prompt, mock_data)
    score = float(result.get("triage_score", 5.0))
    return {
        "triage_score": score,
        "triage_reasoning": result.get("reasoning", ""),
        "is_promising": score >= settings.triage_threshold,
    }


async def scout_node(state: IntelligenceState) -> Dict[str, Any]:
    """Node 2: Extracts technical entities and background context."""
    art = state["article"]
    user_prompt = f"文章标题: {art.title}\n全文: {art.content}"

    mock_data = {
        "entities": ["LangGraph", "StateGraph", "PostgreSQL", "pgvector", "Python 3.11"] if "langgraph" in art.title.lower() else ["HNSW", "pgvector", "Postgres", "FP16 Quantization"],
        "scout_context": "经交叉验证，该技术直接对齐生产级微服务状态机与高效向量召回场景，在生产可用性上有明确文档支撑。",
    }

    result = await llm_client.generate_json(SCOUT_SYSTEM_PROMPT, user_prompt, mock_data)
    return {
        "scout_entities": result.get("entities", []),
        "scout_context": result.get("scout_context", ""),
    }


async def synthesis_node(state: IntelligenceState) -> Dict[str, Any]:
    """Node 3: Synthesizes high-fidelity structured intelligence report."""
    art = state["article"]
    entities = state.get("scout_entities", [])
    scout_context = state.get("scout_context", "")
    critic_feedback = state.get("critic_feedback", "")
    attempt = state.get("attempts", 0) + 1

    user_prompt = (
        f"原标题: {art.title}\n原文内容: {art.content}\n"
        f"探针背景: {scout_context}\n涉及技术实体: {', '.join(entities)}\n"
        f"当前轮次: 第 {attempt} 轮\n"
    )
    if critic_feedback:
        user_prompt += f"\n【必须针对上一轮审查意见严谨修改】: {critic_feedback}\n"

    mock_data = {
        "title": f"【深度评测】{art.title}",
        "summary": f"针对 {art.title} 的关键特性深度拆解与落地选型指引。",
        "background": "在复杂多智能体与超大规模向量检索场景下，传统的简单单向调用与内存索引面临严重稳定性挑战。",
        "core_breakthroughs": [
            "突破性实现 DAG 状态机有状态回环与检查点故障恢复",
            "内存占用降低约 40%~50%，并发索引吞吐大幅提高",
        ],
        "technical_pitfalls": [
            "状态序列化版本兼容性迁移需要妥善管理",
            "极端长链路下重试开销可能造成 API 级联风暴",
        ],
        "engineering_impact": "推荐作为核心基础设施升级考量，需配套熔断监控与死信队列机制。",
        "tags": ["AI-Agent", "System-Architecture", "High-Performance"],
    }

    result = await llm_client.generate_json(SYNTHESIS_SYSTEM_PROMPT, user_prompt, mock_data)
    return {
        "draft_report": result,
        "attempts": attempt,
    }


async def critic_node(state: IntelligenceState) -> Dict[str, Any]:
    """Node 4: Adversarial review of the draft report."""
    draft = state.get("draft_report", {})
    attempt = state.get("attempts", 1)

    user_prompt = (
        f"研报标题: {draft.get('title')}\n"
        f"核心突破: {draft.get('core_breakthroughs')}\n"
        f"工程隐患: {draft.get('technical_pitfalls')}\n"
        f"当前修改轮次: {attempt}\n"
    )

    # In mock mode, purposefully trigger one critique on attempt 1 to demonstrate the Critic Loop
    if attempt == 1:
        mock_data = {
            "critic_passed": False,
            "critic_score": 6.8,
            "feedback": "突破点阐述偏向理想化，未详细说明在极端大并发或网络异常下的失败代价与降级方案，请在工程隐患中补充！",
        }
    else:
        mock_data = {
            "critic_passed": True,
            "critic_score": 9.1,
            "feedback": "论证严谨，平衡了技术优势与边界代价，符合工业级技术决策标准，予以收录！",
        }

    result = await llm_client.generate_json(CRITIC_SYSTEM_PROMPT, user_prompt, mock_data)
    passed = bool(result.get("critic_passed", True))

    # If passed or reached max attempts, finalize the report
    final_intel = None
    if passed or attempt >= settings.max_critic_attempts:
        art = state["article"]
        report_id = hashlib.sha256(f"report:{art.url}".encode()).hexdigest()[:12]
        final_intel = ProcessedIntel(
            id=report_id,
            title=draft.get("title", art.title),
            source_url=art.url,
            source_name=art.source_name,
            triage_score=state.get("triage_score", 8.0),
            summary=draft.get("summary", ""),
            background=draft.get("background", ""),
            core_breakthroughs=draft.get("core_breakthroughs", []),
            technical_pitfalls=draft.get("technical_pitfalls", []),
            engineering_impact=draft.get("engineering_impact", ""),
            key_entities=state.get("scout_entities", []),
            tags=draft.get("tags", []),
            published_at=art.published_at,
            created_at=datetime.now(timezone.utc),
            critic_attempts=attempt,
            critic_verdict="Approved" if passed else "Forced_Pass_Max_Attempts",
        )

    return {
        "critic_passed": passed,
        "critic_score": float(result.get("critic_score", 8.0)),
        "critic_feedback": result.get("feedback", ""),
        "final_intel": final_intel,
    }
