from datetime import datetime, timezone

from src.journal.models import JournalStatus, record_from_signal
from src.journal.store import JournalStore
from src.models.signals import Direction, SignalCandidate


def make_signal(symbol: str = "EURUSD=X") -> SignalCandidate:
    return SignalCandidate(
        symbol=symbol,
        display_symbol="EUR/USD",
        direction=Direction.LONG,
        timeframe="1h",
        entry=1.08421,
        stop_loss=1.08001,
        take_profit=1.09261,
        score=82,
        risk_reward=2.0,
        strategy_tags=("ORDER BLOCK", "FVG"),
        reasons=("valid order block", "fair value gap"),
    )


def test_store_inserts_and_deduplicates_records(tmp_path):
    store = JournalStore(tmp_path / "recommendations.db")
    record = record_from_signal(make_signal(), datetime(2026, 5, 29, tzinfo=timezone.utc))

    assert store.insert_recommendation(record) is True
    assert store.insert_recommendation(record) is False
    assert len(store.list_recommendations()) == 1


def test_store_updates_record_status(tmp_path):
    store = JournalStore(tmp_path / "recommendations.db")
    record = record_from_signal(make_signal(), datetime(2026, 5, 29, tzinfo=timezone.utc))
    store.insert_recommendation(record)

    store.update_resolution(record.signal_key, JournalStatus.TP, 2.0, "TP touched first")
    updated = store.list_recommendations()[0]

    assert updated.status == JournalStatus.TP
    assert updated.outcome_r == 2.0
    assert updated.resolution_note == "TP touched first"
