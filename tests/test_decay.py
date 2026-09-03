"""Tests for time-decay hybrid scoring."""

from datetime import datetime, timezone, timedelta
from nexuspulse.rag.decay import compute_time_decay, hybrid_score


def test_time_decay_bounds_and_monotonicity():
    now = datetime.now(timezone.utc)
    decay_lambda = 0.005

    # Published right now: decay factor should be 1.0
    decay_0h = compute_time_decay(now, reference_time=now, decay_lambda=decay_lambda)
    assert abs(decay_0h - 1.0) < 1e-5

    # Published 24 hours ago
    decay_24h = compute_time_decay(now - timedelta(hours=24), reference_time=now, decay_lambda=decay_lambda)
    assert decay_24h < 1.0
    assert decay_24h > 0.8  # exp(-0.005 * 24) = exp(-0.12) ~= 0.8869

    # Published 7 days ago (168 hours)
    decay_7d = compute_time_decay(now - timedelta(days=7), reference_time=now, decay_lambda=decay_lambda)
    assert decay_7d < decay_24h

    # Monotonicity check: older items must always have smaller decay multipliers
    assert decay_7d < decay_24h < decay_0h


def test_hybrid_score_calculation():
    now = datetime.now(timezone.utc)
    # Identical relevance, but item A is fresh (0h) and item B is 10 days old (240h)
    score_fresh = hybrid_score(
        dense_sim=0.9,
        sparse_sim=0.8,
        published_at=now,
        alpha=0.7,
        reference_time=now,
    )
    score_old = hybrid_score(
        dense_sim=0.9,
        sparse_sim=0.8,
        published_at=now - timedelta(days=10),
        alpha=0.7,
        reference_time=now,
    )

    assert score_fresh > score_old
    assert round(score_fresh, 4) == round(0.7 * 0.9 + 0.3 * 0.8, 4)
