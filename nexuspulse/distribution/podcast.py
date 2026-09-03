"""Cyber podcast generator with Edge-TTS multi-voice synthesis and cognitive conflict."""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import edge_tts

from nexuspulse.ingestion.models import ProcessedIntel
from nexuspulse.agents.llm_client import LLMClient
from nexuspulse.agents.prompts import PODCAST_DIALOGUE_PROMPT
from nexuspulse.config import settings


class CyberPodcastGenerator:
    """Transforms intelligence reports into two-host conversational podcasts."""

    def __init__(
        self,
        voice_a: Optional[str] = None,
        voice_b: Optional[str] = None,
    ):
        self.voice_a = voice_a or settings.podcast_voice_host_a
        self.voice_b = voice_b or settings.podcast_voice_host_b
        self.llm_client = LLMClient()

    async def generate_script(self, intel: ProcessedIntel) -> List[Dict[str, str]]:
        """Generate high-conflict conversational script between Host A and Host B."""
        user_prompt = (
            f"研报主题: {intel.title}\n"
            f"摘要: {intel.summary}\n"
            f"核心突破: {intel.core_breakthroughs}\n"
            f"工程隐患与痛点: {intel.technical_pitfalls}\n"
            f"架构选型建议: {intel.engineering_impact}\n"
        )

        mock_data = {
            "dialogues": [
                {
                    "speaker": "A",
                    "text": f"老陆，今天社区都在疯传《{intel.title}》，说这是划时代的架构突破，你怎么看？",
                },
                {
                    "speaker": "B",
                    "text": "行了吧阿星，别一见发布公告就高潮。底层原理无非是状态持久化与向量降维，真到生产环境还不知道要踩多少坑呢。",
                },
                {
                    "speaker": "A",
                    "text": f"但他们的量化数据很扎实啊！比如这个核心突破：{intel.core_breakthroughs[0] if intel.core_breakthroughs else '大幅提升性能'}，这难道不够硬核吗？",
                },
                {
                    "speaker": "B",
                    "text": f"数据是漂亮的，可你别忘了代价！报告里明确提到了落地隐患：{intel.technical_pitfalls[0] if intel.technical_pitfalls else '极端并发下状态雪崩'}。没有熔断机制上生产就是自杀。",
                },
                {
                    "speaker": "A",
                    "text": "听你这么一拆解确实透彻，那对于咱们普通的工程架构师，当下最明智的行动方案是什么？",
                },
                {
                    "speaker": "B",
                    "text": f"很简单：先用小规模非核心流水线灰度验证，重点关注故障恢复链路。记住，没有银弹，只有权衡。",
                },
            ]
        }

        result = await self.llm_client.generate_json(PODCAST_DIALOGUE_PROMPT, user_prompt, mock_data)
        return result.get("dialogues", mock_data["dialogues"])

    def format_manuscript_markdown(self, intel: ProcessedIntel, dialogues: List[Dict[str, str]]) -> str:
        """Format the dialogue script into a clean, readable Markdown manuscript."""
        lines = [
            "---",
            f'title: "【对谈文稿】{intel.title}"',
            f'source_intel: "{intel.id}"',
            'type: "podcast_manuscript"',
            f'created_at: "{intel.created_at.isoformat()}"',
            f'tags:\n  - TechPodcast\n  - DialogueScript',
            "---",
            "",
            f"# 🎙️ 科技对谈实录：{intel.title}",
            "",
            "> **栏目定位**: 《NexusPulse 赛博茶馆》—— 尖锐发问 vs 毒舌解构  ",
            f"> **关联研报**: [[{intel.title}]] | **原文来源**: [{intel.source_name}]({intel.source_url})  ",
            "> **登场人物**:  ",
            "> - 🧑‍💻 **Host A (阿星)**: 敏锐犀利的科技探究者，直击痛点，追问本质。  ",
            "> - 🧙‍♂️ **Host B (老陆)**: 毒舌硬核的老牌架构师，反感概念炒作，专注底层代价与实战权衡。  ",
            "",
            "---",
            "",
            "## 💬 对谈正文记录 (Transcript)",
            "",
        ]

        for i, line in enumerate(dialogues, 1):
            speaker = line.get("speaker", "A")
            text = line.get("text", "")
            if speaker == "A":
                lines.append(f"**阿星** (Host A) `[{i:02d}]`:")
                lines.append(f"> {text}\n")
            else:
                lines.append(f"**老陆** (Host B) `[{i:02d}]`:")
                lines.append(f"> {text}\n")

        lines.extend([
            "---",
            "",
            "## 📌 老陆的架构备忘录 (Takeaways)",
            f"- **核心警示**: {intel.technical_pitfalls[0] if intel.technical_pitfalls else '谨慎评估状态持久化成本'}",
            f"- **落地法则**: {intel.engineering_impact}",
            "",
            "*本实例文稿由 [[NexusPulse]] 自动生成，纯文本存储，零空间冗余。*",
        ])
        return "\n".join(lines)

    def save_manuscript(self, intel: ProcessedIntel, dialogues: List[Dict[str, str]], output_path: Path) -> Path:
        """Save formatted conversational manuscript to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        md_content = self.format_manuscript_markdown(intel, dialogues)
        output_path.write_text(md_content, encoding="utf-8")
        return output_path

    async def render_audio(self, dialogues: List[Dict[str, str]], output_path: Path) -> Optional[Path]:
        """Synthesize dialogues into multi-track MP3 audio (only if generate_audio is True)."""
        if not settings.generate_audio:
            return None

        output_path.parent.mkdir(parents=True, exist_ok=True)
        audio_segments: List[bytes] = []

        for line in dialogues:
            speaker = line.get("speaker", "A")
            text = line.get("text", "")
            voice = self.voice_a if speaker == "A" else self.voice_b

            communicate = edge_tts.Communicate(text=text, voice=voice)
            buffer = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.extend(chunk["data"])

            if buffer:
                audio_segments.append(bytes(buffer))
                await asyncio.sleep(0.05)

        with open(output_path, "wb") as f:
            for seg in audio_segments:
                f.write(seg)

        return output_path
