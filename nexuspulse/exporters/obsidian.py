"""Obsidian exporter producing bidirectional linked Markdown with YAML frontmatter."""

from pathlib import Path
import re
from nexuspulse.ingestion.models import ProcessedIntel
from nexuspulse.config import settings


class ObsidianExporter:
    """Exports structured reports to an Obsidian vault with wikilinks."""

    def __init__(self, vault_path: Path = None):
        self.vault_path = vault_path or settings.obsidian_vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Clean string for safe filesystem naming."""
        clean = re.sub(r'[\\/*?:"<>|]', "", name)
        return clean.strip().replace(" ", "_")[:80]

    def export_report(self, intel: ProcessedIntel) -> Path:
        """Render report as Markdown and save to Obsidian vault."""
        filename = f"{self._sanitize_filename(intel.title)}.md"
        file_path = self.vault_path / filename

        # Format entities into [[Wikilinks]]
        wikilink_entities = [f"[[{e}]]" for e in intel.key_entities]
        entities_str = ", ".join(wikilink_entities) if wikilink_entities else "无"

        breakthroughs_md = "\n".join([f"- **突破 {i+1}**: {b}" for i, b in enumerate(intel.core_breakthroughs)])
        pitfalls_md = "\n".join([f"- **隐患 {i+1}**: {p}" for i, b, p in zip(range(len(intel.technical_pitfalls)), intel.core_breakthroughs, intel.technical_pitfalls)]) if intel.technical_pitfalls else "- 暂无显著工程隐患"

        tags_yaml = "\n".join([f"  - {t}" for t in intel.tags]) if intel.tags else "  - TechIntel"

        content = f"""---
id: "{intel.id}"
title: "{intel.title}"
source: "{intel.source_name}"
source_url: "{intel.source_url}"
triage_score: {intel.triage_score}
critic_verdict: "{intel.critic_verdict}"
critic_attempts: {intel.critic_attempts}
published_at: "{intel.published_at.isoformat()}"
created_at: "{intel.created_at.isoformat()}"
tags:
{tags_yaml}
---

# 🪐 {intel.title}

> **信噪比评级**: `★ {intel.triage_score}/10.0` | **多智能体审核**: `{intel.critic_verdict}` (第 {intel.critic_attempts} 轮修正通过)  
> **原文链接**: [{intel.source_name}]({intel.source_url})  
> **关联实体图谱**: {entities_str}

---

## 📌 核心摘要 (Executive Summary)
{intel.summary}

## 🔍 技术演化背景 (Context & Motivation)
{intel.background}

## ⚡ 核心技术突破 (Key Breakthroughs)
{breakthroughs_md}

## ⚠️ 落地风险与工程隐患 (Critical Pitfalls & Risks)
{pitfalls_md}

## 🛠️ 架构与选型建议 (Engineering Impact)
{intel.engineering_impact}

---
*自动生成由 [[NexusPulse]] 科技情报中枢*
"""
        file_path.write_text(content, encoding="utf-8")
        return file_path
