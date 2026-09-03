"""NexusPulse interactive CLI and prototype demonstration runner."""

import asyncio
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from nexuspulse.ingestion.fetcher import RSSFetcher
from nexuspulse.ingestion.dedupe import ContentDeduplicator
from nexuspulse.agents.graph import run_intelligence_pipeline
from nexuspulse.rag.chunker import SemanticChunker
from nexuspulse.rag.vector_store import InMemoryVectorStore
from nexuspulse.exporters.obsidian import ObsidianExporter
from nexuspulse.distribution.podcast import CyberPodcastGenerator
from nexuspulse.config import settings

import argparse

console = Console()


async def run_pipeline(live: bool = False, limit: Optional[int] = None):
    """Run full end-to-end intelligence pipeline."""
    limit = limit or settings.max_articles_per_sync
    mode_text = "[bold green]真实全网技术 RSS 实时流[/bold green]" if live else "[dim]内置演示样本流[/dim]"
    console.print(
        Panel.fit(
            "[bold cyan]🪐 NexusPulse: 自主科技情报中枢与混合检索平台[/bold cyan]\n"
            f"[dim]模式: {mode_text} | 单次处理上限: {limit} 篇 | 模型: {settings.llm_model}[/dim]\n"
            "[dim]LangGraph 多智能体 Critic Loop ✕ pgvector 时效混合检索 ✕ FastMCP ✕ 纯文本对谈文稿[/dim]",
            border_style="cyan",
        )
    )

    # ----------------------------------------------------
    # Stage 1: Data Ingestion & Deduplication
    # ----------------------------------------------------
    fetcher = RSSFetcher(timeout=settings.fetch_timeout)
    deduplicator = ContentDeduplicator()

    if live:
        console.print(f"\n[bold yellow]📡 阶段 1: 正在异步连接全网真实 RSS 数据源...[/bold yellow]")
        for name, url in settings.rss_feeds.items():
            console.print(f"  - 订阅源: [cyan]{name}[/cyan] ({url})")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="[cyan]抓取中...[/cyan]", total=None)
            articles = await fetcher.fetch_all_live_feeds(limit_per_feed=3)
    else:
        console.print("\n[bold yellow]📡 阶段 1: 加载技术基准流与指纹去重[/bold yellow]")
        articles = RSSFetcher.get_sample_stream()

    table = Table(title=f"摄取技术线索池 (获取到 {len(articles)} 条)", show_header=True, header_style="bold magenta")
    table.add_column("ID", style="dim", width=10)
    table.add_column("来源", width=18)
    table.add_column("标题", width=42)
    table.add_column("指纹状态", width=15)

    valid_articles = []
    for art in articles:
        if deduplicator.is_duplicate(art.title, art.content):
            status = "[red]重复 (Filtered)[/red]"
        else:
            deduplicator.register(art.id, art.title, art.content)
            status = "[green]新线索 (Unique)[/green]"
            if len(valid_articles) < limit:
                valid_articles.append(art)
            else:
                status += " [dim](排队中)[/dim]"
        table.add_row(art.id[:8] + "...", art.source_name, art.title[:40] + "...", status)

    console.print(table)

    # ----------------------------------------------------
    # Stage 2: LangGraph Multi-Agent Critic Loop
    # ----------------------------------------------------
    console.print("\n[bold yellow]🧠 阶段 2: LangGraph 多智能体反思审查工作流 (Critic Loop)[/bold yellow]")
    vector_store = InMemoryVectorStore()
    exporter = ObsidianExporter()
    podcast_gen = CyberPodcastGenerator()

    processed_reports = []

    for art in valid_articles:
        console.print(f"\n[cyan]正在流转处理条目: [bold]{art.title}[/bold] ({art.source_name})[/cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(description="[cyan]Triage -> Scout -> Synthesis -> Critic...[/cyan]", total=None)
            intel = await run_intelligence_pipeline(art)

        if intel is None:
            console.print(f"  [red]✖ [初筛淘汰][/red] 信噪比过低或属于营销夸大，已被 TriageAgent 拦截丢弃。")
            continue

        console.print(
            f"  [green]✔ [审核通过][/green] 初筛评分: [bold]{intel.triage_score}/10.0[/bold] | "
            f"经历轮次: [bold]{intel.critic_attempts} 轮对抗修正[/bold] | 状态: [bold green]{intel.critic_verdict}[/bold green]"
        )
        console.print(f"  [dim]抽取的关键实体: {', '.join(intel.key_entities)}[/dim]")
        processed_reports.append(intel)

        # ----------------------------------------------------
        # Stage 3: Semantic Chunking & Time-Decayed Hybrid Indexing
        # ----------------------------------------------------
        chunks = SemanticChunker.chunk_intel(intel)
        vector_store.add_chunks(chunks)

        # ----------------------------------------------------
        # Stage 4: Obsidian Export
        # ----------------------------------------------------
        md_file = exporter.export_report(intel)
        console.print(f"  [dim]Obsidian 沉淀: {md_file}[/dim]")

    # ----------------------------------------------------
    # Stage 5: Hybrid Search with Time-Decay Demonstration
    # ----------------------------------------------------
    console.print("\n[bold yellow]🔍 阶段 3: 时效敏感混合检索算法演示 (牛顿冷却时间衰减)[/bold yellow]")
    query = "LangGraph 状态机 故障恢复"
    console.print(f"执行检索关键词: [bold green]\"{query}\"[/bold green] (Alpha=0.7, Lambda={settings.time_decay_lambda})")

    results = vector_store.search_hybrid(query, top_k=3)

    search_table = Table(title="混合检索召回结果", show_header=True, header_style="bold blue")
    search_table.add_column("排名", width=6)
    search_table.add_column("板块", width=18)
    search_table.add_column("Dense向量分", width=12)
    search_table.add_column("Sparse文本分", width=12)
    search_table.add_column("时间衰减因子", width=12)
    search_table.add_column("综合加权得分", style="bold green", width=14)

    for i, r in enumerate(results, 1):
        search_table.add_row(
            str(i),
            r.section,
            str(r.dense_score),
            str(r.sparse_score),
            str(r.time_decay),
            str(r.hybrid_score),
        )
    console.print(search_table)

    # ----------------------------------------------------
    # Stage 6: Cyber Podcast Dialogue Manuscript Generation
    # ----------------------------------------------------
    if processed_reports:
        sample_intel = processed_reports[0]
        console.print(f"\n[bold yellow]🎙️ 阶段 4: 赛博双人对抗播客文稿生成 (零体积纯文本沉淀)[/bold yellow]")
        console.print(f"正在基于研报 [bold]{sample_intel.title}[/bold] 生成认知冲突对谈剧本...")

        dialogues = await podcast_gen.generate_script(sample_intel)
        for line in dialogues[:4]:
            speaker_tag = "[bold green]Host A (阿星)[/bold green]" if line["speaker"] == "A" else "[bold magenta]Host B (老陆)[/bold magenta]"
            console.print(f"  {speaker_tag}: {line['text']}")

        # Save Markdown transcript directly to Obsidian / Project
        manuscript_dir = settings.obsidian_vault_path / "Podcasts"
        manuscript_path = manuscript_dir / f"【对谈文稿】{sample_intel.id}.md"
        saved_doc = podcast_gen.save_manuscript(sample_intel, dialogues, manuscript_path)
        console.print(f"[bold green]✔ 对谈文稿已保存[/bold green]: [cyan]{saved_doc}[/cyan] (纯文本 Markdown 格式，不占存储)")

        if settings.generate_audio:
            output_audio = Path("/tmp/nexus_podcast_sample.mp3")
            console.print(f"正在调用 Edge-TTS 合成音频流...")
            await podcast_gen.render_audio(dialogues[:4], output_audio)
            console.print(f"[green]✔ 音频已生成: {output_audio}[/green]")
        else:
            console.print(f"  [dim]ℹ️ 提示: MP3 音频生成已关闭 (纯文本节约空间模式生效中)[/dim]")

    # ----------------------------------------------------
    # Summary
    # ----------------------------------------------------
    console.print(
        Panel(
            f"[bold green]🎉 NexusPulse 原型全链路验证完成！[/bold green]\n\n"
            f"1. [bold]数据摄取[/bold]: 成功识别并清洗技术资讯，成功拦截营销软文。\n"
            f"2. [bold]LangGraph 回环[/bold]: 经过 Triage -> Scout -> Synthesis -> Critic 完成对抗重写闭环。\n"
            f"3. [bold]混合检索[/bold]: 验证 Dense+Sparse 稠密稀疏双路召回与牛顿冷却时间衰减。\n"
            f"4. [bold]知识沉淀[/bold]: Markdown 研报与双人对谈文稿已写入: [cyan]{settings.obsidian_vault_path}[/cyan]\n"
            f"5. [bold]接口生态[/bold]: 对谈文稿与研报纯文本沉淀；可使用 FastMCP 服务向 Cursor/Claude Code 暴露知识端点。\n\n"
            f"启动 MCP Server: [cyan]python -m nexuspulse.distribution.mcp_server[/cyan]",
            border_style="green",
        )
    )


def main():
    parser = argparse.ArgumentParser(description="NexusPulse Autonomous Tech Intelligence CLI")
    parser.add_argument("--live", action="store_true", help="Connect to real remote RSS feeds instead of sample stream")
    parser.add_argument("--sample", action="store_true", help="Use local sample stream (default)")
    parser.add_argument("--limit", type=int, default=settings.max_articles_per_sync, help="Max articles to process in this run")
    args = parser.parse_args()

    is_live = args.live and not args.sample
    asyncio.run(run_pipeline(live=is_live, limit=args.limit))


if __name__ == "__main__":
    main()
