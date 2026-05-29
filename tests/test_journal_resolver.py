from datetime import datetime, timezone

import pandas as pd

from src.journal.models import JournalStatus, RecommendationRecord
from src.journal.resolver import resolve_recommendation


def make_record(direction: str = "LONG") -> RecommendationRecord:
    return RecommendationRecord(
        signal_key="key",
        created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
        symbol="TEST",
        display_symbol="TEST",
        direction=direction,
        timeframe="1d",
        entry=100.0,
        stop_loss=95.0 if direction == "LONG" else 105.0,
        take_profit=110.0 if direction == "LONG" else 90.0,
        score=80,
        risk_reward=2.0,
        strategy_tags=("ORDER BLOCK",),
        reasons=("valid order block",),
    )


def test_resolve_long_tp_before_sl():
    history = pd.DataFrame({"high": [104.0, 111.0], "low": [99.0, 103.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.TP
    assert result.outcome_r == 2.0


def test_resolve_same_candle_counts_as_sl():
    history = pd.DataFrame({"high": [111.0], "low": [94.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.SL
    assert result.outcome_r == -1.0


def test_resolve_short_tp_before_sl():
    history = pd.DataFrame({"high": [101.0, 99.0], "low": [96.0, 89.0]})

    result = resolve_recommendation(make_record("SHORT"), history)

    assert result.status == JournalStatus.TP
    assert result.outcome_r == 2.0


def test_resolve_keeps_open_when_no_level_hit():
    history = pd.DataFrame({"high": [104.0, 103.0], "low": [99.0, 98.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.OPEN
    assert result.outcome_r is None
