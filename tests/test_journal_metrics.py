from datetime import datetime, timezone

from src.journal.metrics import hit_rate_by_strategy, hit_rate_by_symbol, journal_summary, strategy_feedback_rows
from src.journal.models import JournalStatus, RecommendationRecord


def make_record(
    status: JournalStatus,
    symbol: str = "EURUSD=X",
    tags: tuple[str, ...] = ("ORDER BLOCK",),
    outcome=2.0,
    entry_triggered=True,
):
    return RecommendationRecord(
        signal_key=f"{symbol}-{status.value}-{len(tags)}",
        created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
        symbol=symbol,
        display_symbol=symbol,
        direction="LONG",
        timeframe="1h",
        entry=100,
        stop_loss=95,
        take_profit=110,
        score=80,
        risk_reward=2.0,
        strategy_tags=tags,
        reasons=tags,
        status=status,
        entry_triggered_at=datetime(2026, 5, 29, 1, tzinfo=timezone.utc) if entry_triggered else None,
        outcome_r=outcome if status in {JournalStatus.TP, JournalStatus.SL} else None,
    )


def test_journal_summary_excludes_waiting_and_open_from_hit_rate():
    records = [
        make_record(JournalStatus.TP, outcome=2.0),
        make_record(JournalStatus.SL, outcome=-1.0),
        make_record(JournalStatus.OPEN, outcome=None),
        make_record(JournalStatus.WAITING_ENTRY, outcome=None, entry_triggered=False),
    ]

    summary = journal_summary(records)

    assert summary["total"] == 4
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["open"] == 1
    assert summary["waiting_entry"] == 1
    assert summary["hit_rate"] == 50.0
    assert summary["activation_rate"] == 75.0
    assert summary["average_r"] == 0.5


def test_hit_rate_by_strategy_aggregates_tags():
    records = [
        make_record(JournalStatus.TP, tags=("ORDER BLOCK",), outcome=2.0),
        make_record(JournalStatus.SL, tags=("ORDER BLOCK",), outcome=-1.0),
        make_record(JournalStatus.TP, tags=("FVG",), outcome=2.0),
    ]

    rows = hit_rate_by_strategy(records)

    order_block = next(row for row in rows if row["strategy"] == "ORDER BLOCK")
    assert order_block["hit_rate"] == 50.0


def test_strategy_feedback_rows_include_activation_and_average_r():
    records = [
        make_record(JournalStatus.TP, tags=("ORDER BLOCK",), outcome=2.0),
        make_record(JournalStatus.SL, tags=("ORDER BLOCK",), outcome=-1.0),
        make_record(JournalStatus.WAITING_ENTRY, tags=("ORDER BLOCK",), outcome=None, entry_triggered=False),
    ]

    rows = strategy_feedback_rows(records)

    order_block = next(row for row in rows if row["strategy"] == "ORDER BLOCK")
    assert order_block["waiting_entry"] == 1
    assert order_block["activation_rate"] == 66.67
    assert order_block["average_r"] == 0.5
    assert "confluencia" in order_block["feedback"]


def test_hit_rate_by_symbol_aggregates_symbols():
    records = [
        make_record(JournalStatus.TP, symbol="EURUSD=X", outcome=2.0),
        make_record(JournalStatus.SL, symbol="EURUSD=X", outcome=-1.0),
        make_record(JournalStatus.TP, symbol="GC=F", outcome=2.0),
    ]

    rows = hit_rate_by_symbol(records)

    eur = next(row for row in rows if row["symbol"] == "EURUSD=X")
    assert eur["hit_rate"] == 50.0
