# Command Center Journal Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the approved Command Center journal lifecycle so recommendations track entry activation, TP/SL resolution, and deterministic strategy feedback.

**Architecture:** Extend the existing journal model, resolver, store, and metrics without replacing the current scanner. Add a small feedback module with deterministic rules. Update Streamlit tabs and tables to expose the lifecycle while preserving local SQLite compatibility through additive migration.

**Tech Stack:** Python 3.11+, Streamlit, SQLite, pandas, pytest, Plotly.

---

## File Structure

- Modify `src/journal/models.py`: add `WAITING_ENTRY`, `entry_triggered_at`, and `feedback`; make new records start as waiting for entry.
- Modify `src/journal/resolver.py`: detect entry activation before TP/SL resolution and generate feedback.
- Create `src/journal/feedback.py`: deterministic feedback text and strategy feedback row helpers.
- Modify `src/journal/store.py`: add SQLite columns idempotently and persist new fields.
- Modify `src/journal/metrics.py`: add waiting entry, activation rate, and average R by strategy.
- Modify `app.py`: Command Center tabs, journal rows, feedback tab, updated resolver persistence.
- Modify `tests/test_journal_models.py`, `tests/test_journal_resolver.py`, `tests/test_journal_store.py`, `tests/test_journal_metrics.py`, and `tests/test_app_config.py`.

## Task 1: Journal Model Lifecycle

**Files:**
- Modify: `src/journal/models.py`
- Test: `tests/test_journal_models.py`

- [ ] **Step 1: Write failing tests**

Add tests asserting new signal records start as `WAITING_ENTRY`, expose `entry_triggered_at`, and preserve `feedback`.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_models.py -q`

Expected: failure because `WAITING_ENTRY`, `entry_triggered_at`, or `feedback` does not exist.

- [ ] **Step 3: Implement model fields**

Add `WAITING_ENTRY` to `JournalStatus`, add `entry_triggered_at` and `feedback` to `RecommendationRecord`, and set `record_from_signal(...).status` to `WAITING_ENTRY`.

- [ ] **Step 4: Verify tests pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_models.py -q`

Expected: all model tests pass.

## Task 2: Entry-Aware Resolver

**Files:**
- Modify: `src/journal/resolver.py`
- Create: `src/journal/feedback.py`
- Test: `tests/test_journal_resolver.py`

- [ ] **Step 1: Write failing tests**

Add tests for `WAITING_ENTRY` remaining unchanged when entry is not touched, becoming `OPEN` when entry is touched, resolving TP/SL only after entry, and same-candle TP/SL resolving as SL.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_resolver.py -q`

Expected: failures because the resolver currently checks TP/SL without entry activation.

- [ ] **Step 3: Implement resolver and feedback**

Filter history after `created_at` when possible, detect entry touch, set `entry_triggered_at`, resolve TP/SL after entry, and generate deterministic feedback for TP, SL, waiting, and open states.

- [ ] **Step 4: Verify tests pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_resolver.py -q`

Expected: resolver tests pass.

## Task 3: SQLite Migration And Persistence

**Files:**
- Modify: `src/journal/store.py`
- Test: `tests/test_journal_store.py`

- [ ] **Step 1: Write failing tests**

Add tests that a new store persists `entry_triggered_at` and `feedback`, and an old table without new columns is migrated on initialization.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_store.py -q`

Expected: failures because the store schema does not have the new columns.

- [ ] **Step 3: Implement migration and persistence**

Add an idempotent `_ensure_columns` helper using `PRAGMA table_info`, add missing columns with `ALTER TABLE`, and update inserts, updates, and row mapping.

- [ ] **Step 4: Verify tests pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_store.py -q`

Expected: store tests pass.

## Task 4: Metrics And Feedback Tables

**Files:**
- Modify: `src/journal/metrics.py`
- Modify: `src/journal/feedback.py`
- Test: `tests/test_journal_metrics.py`

- [ ] **Step 1: Write failing tests**

Add tests for waiting entry count, activation rate, average R by strategy, missed entries by strategy, and feedback summary rows.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_metrics.py -q`

Expected: failures because the metrics do not expose the new lifecycle fields.

- [ ] **Step 3: Implement metrics**

Extend `journal_summary`, add strategy lifecycle aggregation, and create feedback insight rows using deterministic text.

- [ ] **Step 4: Verify tests pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_journal_metrics.py -q`

Expected: metric tests pass.

## Task 5: Streamlit Command Center UI

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

- [ ] **Step 1: Write failing tests**

Add tests that `journal_rows` includes entry trigger and feedback, and that feedback row helpers format output for the UI.

- [ ] **Step 2: Run tests to verify failure**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_app_config.py -q`

Expected: failures because UI helpers do not include the new fields yet.

- [ ] **Step 3: Implement UI updates**

Rename tabs to `Buscar`, `Registro`, and `Feedback`; update status filters; persist entry trigger and feedback on resolution; show lifecycle and feedback tables; refine Command Center CSS colors.

- [ ] **Step 4: Verify tests pass**

Run: `.\.venv\Scripts\python.exe -m pytest tests\test_app_config.py -q`

Expected: UI helper tests pass.

## Task 6: Full Verification And Publish

**Files:**
- Modify: none unless verification reveals a defect.

- [ ] **Step 1: Run full tests**

Run: `.\.venv\Scripts\python.exe -m pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Compile**

Run: `.\.venv\Scripts\python.exe -m compileall app.py src`

Expected: exit code 0.

- [ ] **Step 3: Commit and push**

Commit message: `feat: add command center journal feedback`

Push `main` to `origin`.

---

## Self-Review

Spec coverage:

- Recommendation lifecycle: Tasks 1 and 2.
- Journal data and migration: Tasks 1 and 3.
- Feedback logic: Tasks 2 and 4.
- Metrics: Task 4.
- UI details: Task 5.
- Error handling and tests: Tasks 2 through 6.

No placeholders remain. Type names are consistent: `entry_triggered_at`, `feedback`, `WAITING_ENTRY`, `OPEN`, `TP`, `SL`, and `UNRESOLVED`.
