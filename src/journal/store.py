import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.journal.models import JournalStatus, RecommendationRecord


class JournalStore:
    def __init__(self, db_path: str | Path = "data/recommendations.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendations (
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

    def insert_recommendation(self, record: RecommendationRecord) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO recommendations (
                    signal_key, created_at, symbol, display_symbol, direction, timeframe,
                    entry, stop_loss, take_profit, score, risk_reward, strategy_tags,
                    reasons, status, outcome_r, resolved_at, resolution_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.signal_key,
                    record.created_at.isoformat(),
                    record.symbol,
                    record.display_symbol,
                    record.direction,
                    record.timeframe,
                    record.entry,
                    record.stop_loss,
                    record.take_profit,
                    record.score,
                    record.risk_reward,
                    json.dumps(record.strategy_tags),
                    json.dumps(record.reasons),
                    record.status.value,
                    record.outcome_r,
                    record.resolved_at.isoformat() if record.resolved_at else None,
                    record.resolution_note,
                ),
            )
            return cursor.rowcount == 1

    def list_recommendations(self) -> list[RecommendationRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
        return [self._row_to_record(row) for row in rows]

    def update_resolution(
        self,
        signal_key: str,
        status: JournalStatus,
        outcome_r: float,
        resolution_note: str,
        resolved_at: datetime | None = None,
    ) -> None:
        timestamp = resolved_at or datetime.now(timezone.utc)
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE recommendations
                SET status = ?, outcome_r = ?, resolved_at = ?, resolution_note = ?
                WHERE signal_key = ?
                """,
                (status.value, outcome_r, timestamp.isoformat(), resolution_note, signal_key),
            )

    def _row_to_record(self, row: sqlite3.Row) -> RecommendationRecord:
        return RecommendationRecord(
            signal_key=row["signal_key"],
            created_at=datetime.fromisoformat(row["created_at"]),
            symbol=row["symbol"],
            display_symbol=row["display_symbol"],
            direction=row["direction"],
            timeframe=row["timeframe"],
            entry=float(row["entry"]),
            stop_loss=float(row["stop_loss"]),
            take_profit=float(row["take_profit"]),
            score=int(row["score"]),
            risk_reward=float(row["risk_reward"]),
            strategy_tags=tuple(json.loads(row["strategy_tags"])),
            reasons=tuple(json.loads(row["reasons"])),
            status=JournalStatus(row["status"]),
            outcome_r=float(row["outcome_r"]) if row["outcome_r"] is not None else None,
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            resolution_note=row["resolution_note"],
        )
