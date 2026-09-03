"""Newton cooling time-decay scoring algorithm for hybrid retrieval."""

import math
from datetime import datetime, timezone
from typing import Union


def compute_time_decay(
    published_at: datetime,
    reference_time: Union[datetime, None] = None,
    decay_lambda: float = 0.005,
) -> float:
    """Calculate exponential time-decay factor: e^(-lambda * delta_hours).

    Args:
        published_at: Publication timestamp.
        reference_time: Point in time to measure against (default current UTC).
        decay_lambda: Decay rate per hour (e.g. 0.005 ~= half life around 5.7 days).
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    # Ensure timezone awareness
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    delta_seconds = max(0.0, (reference_time - published_at).total_seconds())
    delta_hours = delta_seconds / 3600.0

    decay = math.exp(-decay_lambda * delta_hours)
    return max(0.01, min(1.0, decay))


def hybrid_score(
    dense_sim: float,
    sparse_sim: float,
    published_at: datetime,
    alpha: float = 0.7,
    decay_lambda: float = 0.005,
    reference_time: Union[datetime, None] = None,
) -> float:
    """Calculate time-decayed hybrid score:

    HybridScore = (alpha * dense + (1 - alpha) * sparse) * e^(-lambda * delta_t)
    """
    base_relevance = (alpha * dense_sim) + ((1.0 - alpha) * sparse_sim)
    decay = compute_time_decay(published_at, reference_time, decay_lambda)
    return base_relevance * decay
