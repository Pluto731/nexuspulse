"""Feed fetcher and parser supporting RSS/Atom and mock streams."""

from datetime import datetime, timezone
import hashlib
import time
from typing import List, Optional
import feedparser
import httpx

from nexuspulse.ingestion.models import RawArticle


class RSSFetcher:
    """Fetches and normalizes RSS/Atom items."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    async def fetch_feed(self, feed_url: str, source_name: str) -> List[RawArticle]:
        """Fetch remote RSS/Atom feed asynchronously."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(feed_url)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.text)

        articles = []
        for entry in parsed.entries:
            published_dt = datetime.now(timezone.utc)
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_dt = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed), tz=timezone.utc
                )

            content = ""
            if hasattr(entry, "content") and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, "summary") and entry.summary:
                content = entry.summary
            else:
                content = getattr(entry, "title", "")

            link = getattr(entry, "link", "")
            title = getattr(entry, "title", "Untitled")
            item_id = hashlib.md5(f"{source_name}:{link}".encode()).hexdigest()

            articles.append(
                RawArticle(
                    id=item_id,
                    title=title,
                    url=link,
                    content=content,
                    summary=getattr(entry, "summary", None),
                    source_name=source_name,
                    published_at=published_dt,
                    tags=[t.term for t in getattr(entry, "tags", []) if hasattr(t, "term")],
                )
            )
        return articles

    async def fetch_all_live_feeds(
        self,
        feeds: Optional[dict] = None,
        limit_per_feed: int = 5,
    ) -> List[RawArticle]:
        """Fetch items from multiple remote RSS/Atom feeds concurrently."""
        from nexuspulse.config import settings
        target_feeds = feeds or settings.rss_feeds
        all_articles: List[RawArticle] = []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
            for source_name, url in target_feeds.items():
                try:
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        continue
                    parsed = feedparser.parse(resp.text)
                    count = 0
                    for entry in parsed.entries:
                        if count >= limit_per_feed:
                            break
                        published_dt = datetime.now(timezone.utc)
                        if hasattr(entry, "published_parsed") and entry.published_parsed:
                            published_dt = datetime.fromtimestamp(
                                time.mktime(entry.published_parsed), tz=timezone.utc
                            )

                        content = ""
                        if hasattr(entry, "content") and entry.content:
                            content = entry.content[0].value
                        elif hasattr(entry, "summary") and entry.summary:
                            content = entry.summary
                        else:
                            content = getattr(entry, "title", "")

                        link = getattr(entry, "link", "")
                        title = getattr(entry, "title", "Untitled")
                        item_id = hashlib.md5(f"{source_name}:{link}".encode()).hexdigest()

                        all_articles.append(
                            RawArticle(
                                id=item_id,
                                title=title,
                                url=link,
                                content=content,
                                summary=getattr(entry, "summary", None),
                                source_name=source_name,
                                published_at=published_dt,
                                tags=[t.term for t in getattr(entry, "tags", []) if hasattr(t, "term")],
                            )
                        )
                        count += 1
                except Exception as e:
                    # Ignore temporary network errors for isolated feeds
                    continue

        return all_articles

    @staticmethod
    def get_sample_stream() -> List[RawArticle]:
        """Returns diverse sample articles for local prototype testing."""
        return [
            RawArticle(
                id="art-001",
                title="LangGraph v0.2 Released: Durable Execution & Multi-Agent Human-in-the-Loop",
                url="https://blog.langchain.dev/langgraph-v02",
                content=(
                    "Today we are excited to introduce LangGraph v0.2. It brings native state persistence, "
                    "time-travel debugging, and streaming for cyclic multi-agent graphs. In real-world enterprise "
                    "benchmarks, durability prevents lost state across multi-step LLM chains and allows humans to "
                    "intervene, review, and fork trajectories cleanly."
                ),
                summary="LangGraph 0.2 introduces durable cyclic execution and state persistence.",
                source_name="LangChain Blog",
                tags=["AI", "Agents", "LangGraph"],
            ),
            RawArticle(
                id="art-002",
                title="Shocking! You Won't Believe How This 10-Line Python Script Replaces All Software Engineers!",
                url="https://tech-clickbait.example.com/clickbait-ai-10-lines",
                content=(
                    "Artificial Intelligence is here to take every developer's job today! A programmer wrote 10 lines "
                    "of Python that connects to GPT-4o and creates complete SaaS platforms in 30 seconds. "
                    "Click here to buy our masterclass course for $999 before it's too late!"
                ),
                summary="Sensational claim that 10 lines of script replaces all engineers.",
                source_name="Tech Clickbait Weekly",
                tags=["Marketing", "Clickbait"],
            ),
            RawArticle(
                id="art-003",
                title="pgvector 0.7.0: Sub-millisecond HNSW Indexing and Iterative Index Builds",
                url="https://github.com/pgvector/pgvector/releases/tag/v0.7.0",
                content=(
                    "pgvector 0.7.0 has been released with major performance enhancements. HNSW vector index builds "
                    "are now parallelized, reducing creation times by up to 4x on multi-core servers. It also introduces "
                    "halfvec (FP16) support, reducing index memory footprint by 50% without meaningful loss in recall."
                ),
                summary="pgvector 0.7.0 introduces parallel HNSW builds and FP16 halfvec quantization.",
                source_name="GitHub Releases",
                tags=["Database", "Postgres", "Vector"],
            ),
        ]
