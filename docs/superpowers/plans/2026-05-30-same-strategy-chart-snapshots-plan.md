# Same Strategy Chart Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare chart snapshots only for the same strategy and persist new same-strategy entries with before/after chart JSON.

**Architecture:** Add focused chart snapshot dataclasses/helpers in `src/journal/chart_snapshots.py`, persist them through `JournalStore`, and replace the single `last_chart_snapshot` session value with a keyed dictionary. The app will insert a recommendation and chart snapshot only when the same strategy produces a materially different entry.

**Tech Stack:** Python, Streamlit session state, SQLite, Plotly JSON, pytest.

---

## Task 1: Snapshot Domain Helpers

- [ ] Create tests for same-key comparison and material entry change.
- [ ] Implement `chart_snapshot_key`, `same_snapshot_context`, and `entry_changed`.

## Task 2: Snapshot Storage

- [ ] Create tests for storing and listing chart snapshot records.
- [ ] Add `chart_snapshots` table to `JournalStore`.
- [ ] Add `insert_chart_snapshot` and `list_chart_snapshots`.

## Task 3: App Integration

- [ ] Use `chart_snapshots_by_key` in session state.
- [ ] Show before/after only for same snapshot key.
- [ ] When entry changes, insert a new recommendation and chart snapshot.
- [ ] Show saved chart evolutions in `Registro`.

## Task 4: Verification

- [ ] Run `.\.venv\Scripts\python.exe -m pytest -q`.
- [ ] Run `.\.venv\Scripts\python.exe -m compileall app.py src`.
- [ ] Commit with `feat: persist same strategy chart snapshots`.
- [ ] Push `main`.

## Self-Review

The plan covers same-strategy comparison, new-entry recording, chart snapshot storage, and history review. It intentionally avoids binary image files and external storage.
