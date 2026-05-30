import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from src.journal.chart_snapshots import ChartSnapshotRecord
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
                    entry_triggered_at TEXT,
                    outcome_r REAL,
                    resolved_at TEXT,
                    resolution_note TEXT NOT NULL,
                    feedback TEXT NOT NULL DEFAULT ''
                )
                """
            )
            self._ensure_columns(connection)
            self._init_chart_snapshots(connection)

    def _init_chart_snapshots(self, connection: sqlite3.Connection) -> None:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chart_snapshots (
                snapshot_key TEXT PRIMARY KEY,
                signal_key TEXT NOT NULL,
                created_at TEXT NOT NULL,
                symbol TEXT NOT NULL,
                display_symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                strategy TEXT NOT NULL,
                before_entry REAL NOT NULL,
                before_stop_loss REAL NOT NULL,
                before_take_profit REAL NOT NULL,
                after_entry REAL NOT NULL,
                after_stop_loss REAL NOT NULL,
                after_take_profit REAL NOT NULL,
                before_generated_at TEXT NOT NULL,
                after_generated_at TEXT NOT NULL,
                before_figure_json TEXT NOT NULL,
                after_figure_json TEXT NOT NULL
            )
            """
        )

    def _ensure_columns(self, connection: sqlite3.Connection) -> None:
        existing = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(recommendations)").fetchall()
        }
        if "entry_triggered_at" not in existing:
            connection.execute("ALTER TABLE recommendations ADD COLUMN entry_triggered_at TEXT")
        if "feedback" not in existing:
            connection.execute("ALTER TABLE recommendations ADD COLUMN feedback TEXT NOT NULL DEFAULT ''")

    def insert_recommendation(self, record: RecommendationRecord) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO recommendations (
                    signal_key, created_at, symbol, display_symbol, direction, timeframe,
                    entry, stop_loss, take_profit, score, risk_reward, strategy_tags,
                    reasons, status, entry_triggered_at, outcome_r, resolved_at,
                    resolution_note, feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    record.entry_triggered_at.isoformat() if record.entry_triggered_at else None,
                    record.outcome_r,
                    record.resolved_at.isoformat() if record.resolved_at else None,
                    record.resolution_note,
                    record.feedback,
                ),
            )
            return cursor.rowcount == 1

    def list_recommendations(self) -> list[RecommendationRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM recommendations ORDER BY created_at DESC").fetchall()
        return [self._row_to_record(row) for row in rows]

    def insert_chart_snapshot(self, record: ChartSnapshotRecord) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT OR IGNORE INTO chart_snapshots (
                    snapshot_key, signal_key, created_at, symbol, display_symbol,
                    direction, timeframe, strategy, before_entry, before_stop_loss,
                    before_take_profit, after_entry, after_stop_loss, after_take_profit,
                    before_generated_at, after_generated_at, before_figure_json, after_figure_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.snapshot_key,
                    record.signal_key,
                    record.created_at.isoformat(),
                    record.symbol,
                    record.display_symbol,
                    record.direction,
                    record.timeframe,
                    record.strategy,
                    record.before_entry,
                    record.before_stop_loss,
                    record.before_take_profit,
                    record.after_entry,
                    record.after_stop_loss,
                    record.after_take_profit,
                    record.before_generated_at,
                    record.after_generated_at,
                    record.before_figure_json,
                    record.after_figure_json,
                ),
            )
            return cursor.rowcount == 1

    def list_chart_snapshots(self) -> list[ChartSnapshotRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM chart_snapshots ORDER BY created_at DESC").fetchall()
        return [self._row_to_chart_snapshot(row) for row in rows]

    def update_resolution(
        self,
        signal_key: str,
        status: JournalStatus,
        outcome_r: float | None,
        resolution_note: str,
        resolved_at: datetime | None = None,
        entry_triggered_at: datetime | None = None,
        feedback: str = "",
    ) -> None:
        timestamp = resolved_at or (
            datetime.now(timezone.utc) if status in {JournalStatus.TP, JournalStatus.SL, JournalStatus.UNRESOLVED} else None
        )
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE recommendations
                SET status = ?, entry_triggered_at = COALESCE(?, entry_triggered_at),
                    outcome_r = ?, resolved_at = COALESCE(?, resolved_at),
                    resolution_note = ?, feedback = ?
                WHERE signal_key = ?
                """,
                (
                    status.value,
                    entry_triggered_at.isoformat() if entry_triggered_at else None,
                    outcome_r,
                    timestamp.isoformat() if timestamp else None,
                    resolution_note,
                    feedback,
                    signal_key,
                ),
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
            entry_triggered_at=datetime.fromisoformat(row["entry_triggered_at"]) if row["entry_triggered_at"] else None,
            outcome_r=float(row["outcome_r"]) if row["outcome_r"] is not None else None,
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None,
            resolution_note=row["resolution_note"],
            feedback=row["feedback"],
        )

    def _row_to_chart_snapshot(self, row: sqlite3.Row) -> ChartSnapshotRecord:
        return ChartSnapshotRecord(
            snapshot_key=row["snapshot_key"],
            signal_key=row["signal_key"],
            created_at=datetime.fromisoformat(row["created_at"]),
            symbol=row["symbol"],
            display_symbol=row["display_symbol"],
            direction=row["direction"],
            timeframe=row["timeframe"],
            strategy=row["strategy"],
            before_entry=float(row["before_entry"]),
            before_stop_loss=float(row["before_stop_loss"]),
            before_take_profit=float(row["before_take_profit"]),
            after_entry=float(row["after_entry"]),
            after_stop_loss=float(row["after_stop_loss"]),
            after_take_profit=float(row["after_take_profit"]),
            before_generated_at=row["before_generated_at"],
            after_generated_at=row["after_generated_at"],
            before_figure_json=row["before_figure_json"],
            after_figure_json=row["after_figure_json"],
        )
