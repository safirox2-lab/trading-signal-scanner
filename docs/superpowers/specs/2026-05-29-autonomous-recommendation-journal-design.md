# Autonomous Recommendation Journal - Design

Date: 2026-05-29

## Purpose

Add an autonomous journal to the Trading Signal Scanner so the application records its own recommendations and later evaluates whether each recommendation reached take profit or stop loss first. The journal gives the user a real history of the app's own signals, including hit rate by strategy and symbol.

The journal measures past recommendation outcomes only. It does not guarantee future profitability.

## Approved Direction

Build a local SQLite-backed journal first, with a storage interface that can later be replaced by a cloud database such as Supabase/Postgres if persistent Streamlit Cloud storage is required.

## Recommendation Record

Each recorded recommendation must store:

- Unique recommendation id.
- Created timestamp.
- Symbol and display symbol.
- Direction: `LONG` or `SHORT`.
- Timeframe used by the scanner.
- Entry price.
- Stop loss.
- Take profit.
- Score.
- Risk/reward.
- Strategy tags.
- Reasons/confluences.
- Status:
  - `OPEN`
  - `TP`
  - `SL`
  - `UNRESOLVED`
- Outcome R multiple.
- Resolved timestamp.
- Resolution note.

## Recording Behavior

The app should offer an autonomous recording toggle:

- When enabled, the app records newly generated recommendations.
- Duplicate recommendations should not be repeatedly inserted on every rerun.
- Duplicate detection should use a stable signal key based on symbol, direction, timeframe, rounded entry, rounded stop loss, rounded take profit, and signal date.

The first version should default to manual/autonomous recording through a sidebar toggle named:

```text
Registrar recomendaciones automaticamente
```

This avoids silently writing records unless the user chooses to track them.

## Resolution Behavior

When the app starts or when the journal section is opened, it should evaluate open recommendations using current provider history.

Outcome rules:

- A `LONG` recommendation is a win if future candle high touches or exceeds take profit before future candle low touches or falls below stop loss.
- A `SHORT` recommendation is a win if future candle low touches or falls below take profit before future candle high touches or exceeds stop loss.
- If stop loss is touched first, mark as `SL`.
- If take profit is touched first, mark as `TP`.
- If both are touched in the same candle, use a conservative assumption and mark as `SL`.
- If neither is touched, keep as `OPEN`.
- If data cannot be loaded, keep the record unchanged and show a clear warning in the UI.

Outcome R:

- `TP` should record positive risk/reward, usually `+2.0R`.
- `SL` should record `-1.0R`.
- `OPEN` should not have a final R multiple.

## Metrics

The journal view must show:

- Total recommendations.
- Wins (`TP`).
- Losses (`SL`).
- Open recommendations.
- Overall hit rate.
- Average R.
- Hit rate by strategy.
- Hit rate by symbol.
- Best historical strategy based on resolved recommendations.

Hit rate formula:

```text
TP / (TP + SL) * 100
```

Open and unresolved recommendations must not be counted in the hit-rate denominator.

## User Interface

Add a new section or tab named:

```text
Registro autonomo
```

This section should include:

- Metrics cards for totals and hit rate.
- Table of recommendations.
- Filters by status, symbol, direction, and strategy.
- Button to refresh/evaluate open recommendations.
- Small note explaining that the journal records historical outcomes, not guaranteed future results.

The table should include:

- Created time.
- Symbol.
- Direction.
- Entry.
- SL.
- TP.
- Score.
- Strategies.
- Status.
- Outcome R.
- Resolution note.

## Storage

Use SQLite for the first version:

```text
data/recommendations.db
```

The app should create the `data/` directory and database automatically if missing.

The database file should be ignored by Git:

```text
data/*.db
```

Because Streamlit Community Cloud files can be ephemeral across redeploys/restarts, the UI should include a note:

```text
En Streamlit Cloud, este registro local puede reiniciarse. Para persistencia real en la nube, conecta Supabase/Postgres.
```

## Testing Plan

Unit tests:

- Recommendation model creates a stable signal key.
- SQLite store inserts and deduplicates recommendations.
- SQLite store lists recommendations.
- Outcome resolver marks TP before SL correctly.
- Outcome resolver marks same-candle TP/SL as SL.
- Metrics exclude OPEN records from hit-rate denominator.
- Strategy and symbol hit-rate aggregation works.

Manual verification:

- Run Streamlit locally.
- Enable automatic recording.
- Generate recommendations.
- Confirm records appear in `Registro autonomo`.
- Refresh/evaluate open recommendations.
- Confirm metrics update after records resolve.

## Out Of Scope

- Broker execution.
- Auto-trading.
- Cloud database setup in the first version.
- User accounts.
- Multi-device synchronization.
- Treating journal hit rate as guaranteed future probability.

## Files To Add Or Modify

- Modify: `.gitignore`
- Modify: `app.py`
- Create: `src/journal/__init__.py`
- Create: `src/journal/models.py`
- Create: `src/journal/store.py`
- Create: `src/journal/resolver.py`
- Create: `src/journal/metrics.py`
- Create: `tests/test_journal_models.py`
- Create: `tests/test_journal_store.py`
- Create: `tests/test_journal_resolver.py`
- Create: `tests/test_journal_metrics.py`
