from datetime import datetime, timezone

from src.journal.models import JournalStatus, RecommendationRecord, record_from_signal, stable_signal_key
from src.models.signals import Direction, SignalCandidate


def make_signal() -> SignalCandidate:
    return SignalCandidate(
        symbol="EURUSD=X",
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


def test_stable_signal_key_uses_price_levels_and_date():
    created = datetime(2026, 5, 29, 12, 30, tzinfo=timezone.utc)

    key = stable_signal_key(make_signal(), created)

    assert key == "EURUSD=X|LONG|1h|1.08421|1.08001|1.09261|2026-05-29"


def test_record_from_signal_defaults_to_open_status():
    created = datetime(2026, 5, 29, 12, 30, tzinfo=timezone.utc)

    record = record_from_signal(make_signal(), created)

    assert isinstance(record, RecommendationRecord)
    assert record.status == JournalStatus.OPEN
    assert record.outcome_r is None
    assert record.strategy_tags == ("ORDER BLOCK", "FVG")
