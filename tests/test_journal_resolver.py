from datetime import datetime, timezone

import pandas as pd

from src.journal.models import JournalStatus, RecommendationRecord
from src.journal.resolver import resolve_recommendation


def make_record(direction: str = "LONG", status: JournalStatus = JournalStatus.WAITING_ENTRY) -> RecommendationRecord:
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
        status=status,
    )


def test_waiting_entry_remains_waiting_when_entry_not_touched():
    history = pd.DataFrame({"high": [99.0, 99.5], "low": [96.0, 97.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.WAITING_ENTRY
    assert result.entry_triggered_at is None
    assert result.outcome_r is None
    assert "Entrada aun no activada" in result.feedback


def test_waiting_entry_becomes_open_when_entry_touched_without_exit():
    history = pd.DataFrame({"high": [101.0], "low": [99.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.OPEN
    assert result.entry_triggered_at is not None
    assert result.outcome_r is None


def test_resolve_long_tp_after_entry():
    history = pd.DataFrame({"high": [101.0, 111.0], "low": [99.0, 103.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.TP
    assert result.entry_triggered_at is not None
    assert result.outcome_r == 2.0
    assert "TP alcanzado" in result.feedback


def test_resolve_same_candle_after_entry_counts_as_sl():
    history = pd.DataFrame({"high": [111.0], "low": [94.0]})

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.SL
    assert result.outcome_r == -1.0
    assert "SL alcanzado" in result.feedback


def test_resolve_short_tp_before_sl():
    history = pd.DataFrame({"high": [101.0, 99.0], "low": [96.0, 89.0]})

    result = resolve_recommendation(make_record("SHORT"), history)

    assert result.status == JournalStatus.TP
    assert result.outcome_r == 2.0


def test_resolve_ignores_candles_before_recommendation_time():
    history = pd.DataFrame(
        {"high": [101.0, 101.0, 111.0], "low": [94.0, 99.0, 103.0]},
        index=pd.to_datetime(
            [
                "2026-05-28T23:00:00Z",
                "2026-05-29T00:00:00Z",
                "2026-05-29T01:00:00Z",
            ]
        ),
    )

    result = resolve_recommendation(make_record("LONG"), history)

    assert result.status == JournalStatus.TP
    assert result.resolved_at.isoformat() == "2026-05-29T01:00:00+00:00"


def test_resolve_keeps_open_when_no_level_hit():
    history = pd.DataFrame({"high": [104.0, 103.0], "low": [99.0, 98.0]})

    result = resolve_recommendation(make_record("LONG", status=JournalStatus.OPEN), history)

    assert result.status == JournalStatus.OPEN
    assert result.outcome_r is None
