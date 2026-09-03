"""Data ingestion, normalization, and deduplication modules."""

from nexuspulse.ingestion.models import RawArticle, ProcessedIntel
from nexuspulse.ingestion.dedupe import ContentDeduplicator
from nexuspulse.ingestion.fetcher import RSSFetcher

__all__ = ["RawArticle", "ProcessedIntel", "ContentDeduplicator", "RSSFetcher"]
