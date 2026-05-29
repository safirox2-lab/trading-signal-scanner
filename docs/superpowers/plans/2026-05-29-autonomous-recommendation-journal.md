# Autonomous Recommendation Journal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local autonomous journal that records the app's recommendations, resolves TP/SL outcomes, and reports hit-rate metrics by strategy and symbol.

**Architecture:** Add a `src/journal` package with pure model, SQLite storage, resolver, and metrics modules. Streamlit will call these modules from a new `Registro autonomo` tab while keeping scanner/chart logic separate.

**Tech Stack:** Python 3, Streamlit, SQLite standard library, Pandas, pytest.

---

## File Structure

- Modify: `.gitignore` to ignore local SQLite journal files.
- Modify: `app.py` to add recording toggle and `Registro autonomo` tab.
- Create: `src/journal/__init__.py` package initializer.
- Create: `src/journal/models.py` for recommendation records, statuses, and stable signal keys.
- Create: `src/journal/store.py` for SQLite schema, insert/deduplicate, list, and update.
- Create: `src/journal/resolver.py` for TP/SL outcome resolution.
- Create: `src/journal/metrics.py` for hit-rate, average R, and grouped metrics.
- Create: `tests/test_journal_models.py`.
- Create: `tests/test_journal_store.py`.
- Create: `tests/test_journal_resolver.py`.
- Create: `tests/test_journal_metrics.py`.

## Task 1: Journal Models And Stable Keys

**Files:**
- Create: `src/journal/__init__.py`
- Create: `src/journal/models.py`
- Test: `tests/test_journal_models.py`

- [ ] **Step 1: Write failing model tests**

Write `tests/test_journal_models.py`:

```python
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
```

- [ ] **Step 2: Run model tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_models.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.journal'`.

- [ ] **Step 3: Create journal package initializer**

Write `src/journal/__init__.py`:

```python
"""Autonomous recommendation journal."""
```

- [ ] **Step 4: Implement journal models**

Write `src/journal/models.py`:

```python
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from src.models.signals import SignalCandidate


class JournalStatus(str, Enum):
    OPEN = "OPEN"
    TP = "TP"
    SL = "SL"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class RecommendationRecord:
    signal_key: str
    created_at: datetime
    symbol: str
    display_symbol: str
    direction: str
    timeframe: str
    entry: float
    stop_loss: float
    take_profit: float
    score: int
    risk_reward: float
    strategy_tags: tuple[str, ...]
    reasons: tuple[str, ...]
    status: JournalStatus = JournalStatus.OPEN
    outcome_r: float | None = None
    resolved_at: datetime | None = None
    resolution_note: str = ""


def stable_signal_key(signal: SignalCandidate, created_at: datetime | None = None) -> str:
    timestamp = created_at or datetime.now(timezone.utc)
    signal_date = timestamp.date().isoformat()
    return "|".join(
        [
            signal.symbol,
            signal.direction.value,
            signal.timeframe,
            f"{signal.entry:.5f}",
            f"{signal.stop_loss:.5f}",
            f"{signal.take_profit:.5f}",
            signal_date,
        ]
    )


def record_from_signal(signal: SignalCandidate, created_at: datetime | None = None) -> RecommendationRecord:
    timestamp = created_at or datetime.now(timezone.utc)
    return RecommendationRecord(
        signal_key=stable_signal_key(signal, timestamp),
        created_at=timestamp,
        symbol=signal.symbol,
        display_symbol=signal.display_symbol,
        direction=signal.direction.value,
        timeframe=signal.timeframe,
        entry=signal.entry,
        stop_loss=signal.stop_loss,
        take_profit=signal.take_profit,
        score=signal.score,
        risk_reward=signal.risk_reward,
        strategy_tags=signal.strategy_tags,
        reasons=signal.reasons,
    )
```

- [ ] **Step 5: Run model tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_models.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit journal models**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/journal tests/test_journal_models.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add recommendation journal models"
```

Expected: commit succeeds.

## Task 2: SQLite Journal Store

**Files:**
- Create: `src/journal/store.py`
- Test: `tests/test_journal_store.py`

- [ ] **Step 1: Write failing store tests**

Write `tests/test_journal_store.py`:

```python
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
```

- [ ] **Step 2: Run store tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_store.py -v
```

Expected: FAIL with missing `src.journal.store`.

- [ ] **Step 3: Implement SQLite store**

Write `src/journal/store.py`:

```python
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
```

- [ ] **Step 4: Run store tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_store.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit SQLite store**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/journal/store.py tests/test_journal_store.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: store recommendation journal in sqlite"
```

Expected: commit succeeds.

## Task 3: Recommendation Resolver

**Files:**
- Create: `src/journal/resolver.py`
- Test: `tests/test_journal_resolver.py`

- [ ] **Step 1: Write failing resolver tests**

Write `tests/test_journal_resolver.py`:

```python
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
```

- [ ] **Step 2: Run resolver tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_resolver.py -v
```

Expected: FAIL with missing `src.journal.resolver`.

- [ ] **Step 3: Implement resolver**

Write `src/journal/resolver.py`:

```python
from dataclasses import replace
from datetime import datetime, timezone

import pandas as pd

from src.journal.models import JournalStatus, RecommendationRecord


def resolve_recommendation(record: RecommendationRecord, history: pd.DataFrame) -> RecommendationRecord:
    if record.status != JournalStatus.OPEN:
        return record
    for _, candle in history.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if record.direction == "LONG":
            stop_hit = low <= record.stop_loss
            target_hit = high >= record.take_profit
        else:
            stop_hit = high >= record.stop_loss
            target_hit = low <= record.take_profit
        if stop_hit:
            return replace(
                record,
                status=JournalStatus.SL,
                outcome_r=-1.0,
                resolved_at=datetime.now(timezone.utc),
                resolution_note="SL touched before TP or same candle as TP",
            )
        if target_hit:
            return replace(
                record,
                status=JournalStatus.TP,
                outcome_r=record.risk_reward,
                resolved_at=datetime.now(timezone.utc),
                resolution_note="TP touched before SL",
            )
    return record
```

- [ ] **Step 4: Run resolver tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_resolver.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit resolver**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/journal/resolver.py tests/test_journal_resolver.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: resolve journal recommendations"
```

Expected: commit succeeds.

## Task 4: Journal Metrics

**Files:**
- Create: `src/journal/metrics.py`
- Test: `tests/test_journal_metrics.py`

- [ ] **Step 1: Write failing metrics tests**

Write `tests/test_journal_metrics.py`:

```python
from datetime import datetime, timezone

from src.journal.metrics import hit_rate_by_strategy, hit_rate_by_symbol, journal_summary
from src.journal.models import JournalStatus, RecommendationRecord


def make_record(status: JournalStatus, symbol: str = "EURUSD=X", tags: tuple[str, ...] = ("ORDER BLOCK",), outcome=2.0):
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
        outcome_r=outcome if status in {JournalStatus.TP, JournalStatus.SL} else None,
    )


def test_journal_summary_excludes_open_from_hit_rate():
    records = [
        make_record(JournalStatus.TP, outcome=2.0),
        make_record(JournalStatus.SL, outcome=-1.0),
        make_record(JournalStatus.OPEN, outcome=None),
    ]

    summary = journal_summary(records)

    assert summary["total"] == 3
    assert summary["wins"] == 1
    assert summary["losses"] == 1
    assert summary["open"] == 1
    assert summary["hit_rate"] == 50.0
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


def test_hit_rate_by_symbol_aggregates_symbols():
    records = [
        make_record(JournalStatus.TP, symbol="EURUSD=X", outcome=2.0),
        make_record(JournalStatus.SL, symbol="EURUSD=X", outcome=-1.0),
        make_record(JournalStatus.TP, symbol="GC=F", outcome=2.0),
    ]

    rows = hit_rate_by_symbol(records)

    eur = next(row for row in rows if row["symbol"] == "EURUSD=X")
    assert eur["hit_rate"] == 50.0
```

- [ ] **Step 2: Run metrics tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_metrics.py -v
```

Expected: FAIL with missing `src.journal.metrics`.

- [ ] **Step 3: Implement metrics**

Write `src/journal/metrics.py`:

```python
from collections import defaultdict

from src.journal.models import JournalStatus, RecommendationRecord


def _hit_rate(wins: int, losses: int) -> float:
    resolved = wins + losses
    return round((wins / resolved) * 100, 2) if resolved else 0.0


def journal_summary(records: list[RecommendationRecord]) -> dict[str, float | int]:
    wins = len([record for record in records if record.status == JournalStatus.TP])
    losses = len([record for record in records if record.status == JournalStatus.SL])
    open_count = len([record for record in records if record.status == JournalStatus.OPEN])
    resolved_r = [record.outcome_r for record in records if record.outcome_r is not None]
    return {
        "total": len(records),
        "wins": wins,
        "losses": losses,
        "open": open_count,
        "hit_rate": _hit_rate(wins, losses),
        "average_r": round(sum(resolved_r) / len(resolved_r), 2) if resolved_r else 0.0,
    }


def hit_rate_by_strategy(records: list[RecommendationRecord]) -> list[dict[str, float | int | str]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0})
    for record in records:
        if record.status not in {JournalStatus.TP, JournalStatus.SL}:
            continue
        for tag in record.strategy_tags:
            if record.status == JournalStatus.TP:
                buckets[tag]["wins"] += 1
            else:
                buckets[tag]["losses"] += 1
    return [
        {
            "strategy": strategy,
            "wins": values["wins"],
            "losses": values["losses"],
            "hit_rate": _hit_rate(values["wins"], values["losses"]),
        }
        for strategy, values in sorted(buckets.items())
    ]


def hit_rate_by_symbol(records: list[RecommendationRecord]) -> list[dict[str, float | int | str]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0})
    for record in records:
        if record.status not in {JournalStatus.TP, JournalStatus.SL}:
            continue
        if record.status == JournalStatus.TP:
            buckets[record.symbol]["wins"] += 1
        else:
            buckets[record.symbol]["losses"] += 1
    return [
        {
            "symbol": symbol,
            "wins": values["wins"],
            "losses": values["losses"],
            "hit_rate": _hit_rate(values["wins"], values["losses"]),
        }
        for symbol, values in sorted(buckets.items())
    ]
```

- [ ] **Step 4: Run metrics tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_journal_metrics.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit metrics**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/journal/metrics.py tests/test_journal_metrics.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: calculate recommendation journal metrics"
```

Expected: commit succeeds.

## Task 5: Streamlit Journal UI And Recording Flow

**Files:**
- Modify: `.gitignore`
- Modify: `app.py`
- Test: `tests/test_app_config.py`

- [ ] **Step 1: Extend app tests for journal row formatting**

Append to `tests/test_app_config.py`:

```python
from datetime import datetime, timezone

from app import journal_rows
from src.journal.models import JournalStatus, RecommendationRecord


def test_journal_rows_formats_records_for_table():
    record = RecommendationRecord(
        signal_key="key",
        created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction="LONG",
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=("ORDER BLOCK",),
        reasons=("valid order block",),
        status=JournalStatus.TP,
        outcome_r=2.0,
        resolution_note="TP touched before SL",
    )

    rows = journal_rows([record])

    assert rows[0]["Symbol"] == "EUR/USD"
    assert rows[0]["Status"] == "TP"
    assert rows[0]["Outcome R"] == 2.0
```

- [ ] **Step 2: Run app tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_config.py -v
```

Expected: FAIL because `journal_rows` does not exist.

- [ ] **Step 3: Ignore SQLite journal files**

Modify `.gitignore` to include:

```text
data/*.db
```

- [ ] **Step 4: Add journal imports and helpers to `app.py`**

Add imports:

```python
from src.journal.metrics import hit_rate_by_strategy, hit_rate_by_symbol, journal_summary
from src.journal.models import JournalStatus, RecommendationRecord, record_from_signal
from src.journal.resolver import resolve_recommendation
from src.journal.store import JournalStore
```

Add helper below `load_history`:

```python
def journal_rows(records: list[RecommendationRecord]) -> list[dict[str, str | int | float | None]]:
    return [
        {
            "Created": record.created_at.strftime("%Y-%m-%d %H:%M"),
            "Symbol": record.display_symbol,
            "Direction": record.direction,
            "Entry": record.entry,
            "SL": record.stop_loss,
            "TP": record.take_profit,
            "Score": record.score,
            "Strategies": ", ".join(record.strategy_tags),
            "Status": record.status.value,
            "Outcome R": record.outcome_r,
            "Note": record.resolution_note,
        }
        for record in records
    ]
```

- [ ] **Step 5: Add recording toggle and tabs in `app.py`**

Inside sidebar, add:

```python
        auto_record = st.toggle("Registrar recomendaciones automaticamente", value=False)
```

After scanning and sorting signals, add:

```python
    store = JournalStore()
    if auto_record:
        for signal in signals:
            store.insert_recommendation(record_from_signal(signal))

    scanner_tab, journal_tab = st.tabs(["Scanner", "Registro autonomo"])
```

Move the existing opportunities/chart UI inside:

```python
    with scanner_tab:
        ...
```

Add journal UI after scanner tab:

```python
    with journal_tab:
        st.subheader("Registro autonomo")
        st.caption(
            "Este registro mide resultados historicos de recomendaciones guardadas. "
            "En Streamlit Cloud, el registro local puede reiniciarse; para persistencia real conecta Supabase/Postgres."
        )
        if st.button("Actualizar recomendaciones abiertas"):
            updated_count = 0
            for record in store.list_recommendations():
                if record.status != JournalStatus.OPEN:
                    continue
                try:
                    history = load_history(record.symbol, period="730d", interval=record.timeframe)
                    updated = resolve_recommendation(record, history)
                    if updated.status != record.status and updated.outcome_r is not None:
                        store.update_resolution(
                            record.signal_key,
                            updated.status,
                            updated.outcome_r,
                            updated.resolution_note,
                            updated.resolved_at,
                        )
                        updated_count += 1
                except Exception as exc:
                    st.warning(f"No se pudo evaluar {record.display_symbol}: {exc}")
            st.success(f"Recomendaciones actualizadas: {updated_count}")

        records = store.list_recommendations()
        summary = journal_summary(records)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total", summary["total"])
        m2.metric("TP", summary["wins"])
        m3.metric("SL", summary["losses"])
        m4.metric("Abiertas", summary["open"])
        m5.metric("% acierto", f'{summary["hit_rate"]:.1f}%')
        st.metric("Average R", summary["average_r"])

        if records:
            statuses = ["ALL"] + sorted({record.status.value for record in records})
            selected_status = st.selectbox("Filtrar estado", statuses)
            filtered = records if selected_status == "ALL" else [record for record in records if record.status.value == selected_status]
            st.dataframe(journal_rows(filtered), use_container_width=True, hide_index=True)

            st.subheader("Acierto por estrategia")
            st.dataframe(hit_rate_by_strategy(records), use_container_width=True, hide_index=True)

            st.subheader("Acierto por simbolo")
            st.dataframe(hit_rate_by_symbol(records), use_container_width=True, hide_index=True)
        else:
            st.info("Aun no hay recomendaciones registradas.")
```

- [ ] **Step 6: Run app config tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_config.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit UI integration**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add .gitignore app.py tests/test_app_config.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add autonomous recommendation journal UI"
```

Expected: commit succeeds.

## Task 6: Verification, Docs, And Publish

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Update README**

Append to `README.md`:

```markdown
## Autonomous Recommendation Journal

Enable `Registrar recomendaciones automaticamente` to store generated recommendations in a local SQLite journal. The `Registro autonomo` tab evaluates open recommendations against available market history and reports TP/SL outcomes, hit rate, average R, and hit rate by strategy and symbol.

Local journal data is stored in `data/recommendations.db` and is ignored by Git. On Streamlit Community Cloud, local file persistence may reset across redeploys or restarts; use an external database such as Supabase/Postgres for durable cloud history.
```

- [ ] **Step 3: Commit docs**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add README.md
& 'C:\Program Files\Git\cmd\git.exe' commit -m "docs: describe autonomous recommendation journal"
```

Expected: commit succeeds.

- [ ] **Step 4: Restart local Streamlit**

Run outside sandbox if needed:

```powershell
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process
.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Expected: app starts at `http://127.0.0.1:8501`.

- [ ] **Step 5: Verify local port**

Run:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8501
```

Expected: `TcpTestSucceeded : True`.

- [ ] **Step 6: Push to GitHub**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' push
```

Expected: branch `main` pushes to `origin/main`.

## Self-Review

Spec coverage:

- Recommendation record fields are covered by Task 1.
- SQLite storage, auto-create database, and deduplication are covered by Task 2.
- Conservative TP/SL resolution is covered by Task 3.
- Hit-rate, average R, and grouped metrics are covered by Task 4.
- Streamlit journal tab, toggle, update button, and cloud persistence note are covered by Task 5.
- README and GitHub publishing are covered by Task 6.

No placeholders are intentionally left. The design records historical outcomes only and does not imply guaranteed future success.
