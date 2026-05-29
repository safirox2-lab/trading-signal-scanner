from datetime import datetime, timezone
import sqlite3

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

    entry_time = datetime(2026, 5, 29, 13, 0, tzinfo=timezone.utc)
    store.update_resolution(
        record.signal_key,
        JournalStatus.TP,
        2.0,
        "TP touched first",
        entry_triggered_at=entry_time,
        feedback="TP alcanzado.",
    )
    updated = store.list_recommendations()[0]

    assert updated.status == JournalStatus.TP
    assert updated.entry_triggered_at == entry_time
    assert updated.outcome_r == 2.0
    assert updated.resolution_note == "TP touched first"
    assert updated.feedback == "TP alcanzado."


def test_store_migrates_legacy_database(tmp_path):
    db_path = tmp_path / "legacy.db"
    with sqlite3.connect(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE recommendations (
                signal_key TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                display_symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                entry REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                score INTEGER NOT NULL,
                risk_reward REAL NOT NULL,
                strategy_tags TEXT NOT NULL,
                reasons TEXT NOT NULL,
                status TEXT NOT NULL,
                outcome_r REAL,
                resolved_at TEXT,
                resolution_note TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO recommendations (
                signal_key, created_at, symbol, display_symbol, direction, timeframe,
                entry, stop_loss, take_profit, score, risk_reward, strategy_tags,
                reasons, status, outcome_r, resolved_at, resolution_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy",
                datetime(2026, 5, 29, tzinfo=timezone.utc).isoformat(),
                "EURUSD=X",
                "EUR/USD",
                "LONG",
                "1h",
                1.08,
                1.07,
                1.1,
                80,
                2.0,
                '["ORDER BLOCK"]',
                '["valid order block"]',
                "OPEN",
                None,
                None,
                "",
            ),
        )

    store = JournalStore(db_path)
    record = store.list_recommendations()[0]

    assert record.signal_key == "legacy"
    assert record.entry_triggered_at is None
    assert record.feedback == ""
