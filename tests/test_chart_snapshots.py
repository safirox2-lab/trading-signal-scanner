from datetime import datetime, timezone

from src.journal.chart_snapshots import ChartSnapshotRecord, chart_snapshot_key, entry_changed, same_snapshot_context


def make_snapshot(strategy: str = "Order Block", entry: float = 1.2345) -> dict[str, str | float]:
    return {
        "symbol": "USD/CAD",
        "interval": "1d",
        "period": "max",
        "strategy": strategy,
        "entry": entry,
        "stop_loss": 1.23,
        "take_profit": 1.25,
        "direction": "SHORT",
        "generated_at": "2026-05-30 00:00:00",
    }


def test_chart_snapshot_key_uses_same_strategy_context():
    snapshot = make_snapshot()

    assert chart_snapshot_key(snapshot) == "USD/CAD|1d|SHORT|Order Block"


def test_same_snapshot_context_requires_same_strategy():
    before = make_snapshot("Order Block")
    after = make_snapshot("FVG / Imbalance")

    assert same_snapshot_context(before, after) is False
    assert same_snapshot_context(before, make_snapshot("Order Block")) is True


def test_entry_changed_uses_tolerance():
    before = make_snapshot(entry=1.23450)
    tiny_move = make_snapshot(entry=1.23454)
    real_move = make_snapshot(entry=1.23600)

    assert entry_changed(before, tiny_move, tolerance=0.0001) is False
    assert entry_changed(before, real_move, tolerance=0.0001) is True


def test_chart_snapshot_record_has_review_fields():
    record = ChartSnapshotRecord(
        snapshot_key="key",
        signal_key="signal",
        created_at=datetime(2026, 5, 30, tzinfo=timezone.utc),
        symbol="USDCAD=X",
        display_symbol="USD/CAD",
        direction="SHORT",
        timeframe="1d",
        strategy="Order Block",
        before_entry=1.2345,
        before_stop_loss=1.24,
        before_take_profit=1.22,
        after_entry=1.236,
        after_stop_loss=1.242,
        after_take_profit=1.224,
        before_generated_at="2026-05-30 00:00:00",
        after_generated_at="2026-05-30 00:05:00",
        before_figure_json='{"before": true}',
        after_figure_json='{"after": true}',
    )

    assert record.strategy == "Order Block"
    assert record.after_entry == 1.236
