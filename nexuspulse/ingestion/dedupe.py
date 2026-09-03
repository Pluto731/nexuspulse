"""Deduplication engine based on SHA256 content fingerprints and title similarity."""

import hashlib
import re
from typing import Set, Dict


class ContentDeduplicator:
    """Manages exact and near-duplicate filtering of news feeds."""

    def __init__(self, sim_threshold: float = 0.85):
        self.sim_threshold = sim_threshold
        self._exact_hashes: Set[str] = set()
        self._seen_titles: Dict[str, str] = {}  # normalized_title -> item_id

    @staticmethod
    def normalize_text(text: str) -> str:
        """Strip HTML, non-alphanumeric noise, and multiple spaces."""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip().lower()
        return text

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 fingerprint of normalized content."""
        normalized = self.normalize_text(content)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _token_jaccard(self, str1: str, str2: str) -> float:
        """Jaccard similarity on token sets."""
        tokens1 = set(re.findall(r"\w+", str1.lower()))
        tokens2 = set(re.findall(r"\w+", str2.lower()))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0

    def is_duplicate(self, title: str, content: str) -> bool:
        """Check if article is duplicate by content hash or title similarity."""
        content_hash = self.compute_hash(content)
        if content_hash in self._exact_hashes:
            return True

        norm_title = self.normalize_text(title)
        for seen_title in self._seen_titles.keys():
            if self._token_jaccard(norm_title, seen_title) >= self.sim_threshold:
                return True

        return False

    def register(self, item_id: str, title: str, content: str) -> None:
        """Register an item to the deduplication index."""
        content_hash = self.compute_hash(content)
        self._exact_hashes.add(content_hash)
        norm_title = self.normalize_text(title)
        self._seen_titles[norm_title] = item_id
