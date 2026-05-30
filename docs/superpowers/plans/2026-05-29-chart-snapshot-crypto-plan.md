# Chart Snapshot And Crypto Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the previous chart visible while a new strategy chart is calculated, show before/after trade-level comparison, and add crypto symbols to the scanner.

**Architecture:** Add crypto symbols to the existing provider symbol list. Add small pure helpers in `app.py` for chart snapshot metadata and comparison rows, then use `st.session_state` as a local double buffer around the existing cached Plotly figure path.

**Tech Stack:** Python, Streamlit session state, Plotly, yfinance symbols, pytest.

---

## Task 1: Crypto Symbols

**Files:**
- Modify: `src/data/providers.py`
- Test: `tests/test_models.py`

- [ ] Write a failing test that `default_symbols()` includes market `crypto` with BTC, ETH, SOL, BNB, XRP, ADA, and DOGE Yahoo Finance provider symbols.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests\test_models.py -q` and confirm it fails.
- [ ] Add the crypto `MarketSymbol` records.
- [ ] Run the same test and confirm it passes.

## Task 2: Chart Snapshot Helpers

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

- [ ] Write failing tests for `chart_snapshot_metadata(...)` and `chart_comparison_rows(...)`.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests\test_app_config.py -q` and confirm it fails.
- [ ] Implement helpers that store strategy, entry, SL, TP, direction, symbol, interval, period, and generated timestamp.
- [ ] Run the same test and confirm it passes.

## Task 3: Before/After Chart Rendering

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

- [ ] Use `st.session_state["last_chart_snapshot"]` to keep the previous chart visible.
- [ ] Add a `Mostrar comparacion antes/despues` toggle, enabled by default.
- [ ] Render two columns when a previous chart exists: `Antes` and `Despues`.
- [ ] Show comparison rows for strategy, entry, SL, TP, symbol, and interval.
- [ ] Save the current chart snapshot after rendering.
- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests\test_app_config.py -q`.

## Task 4: Verification And Publish

- [ ] Run `.\.venv\Scripts\python.exe -m pytest -q`.
- [ ] Run `.\.venv\Scripts\python.exe -m compileall app.py src`.
- [ ] Commit with `feat: add chart snapshots and crypto markets`.
- [ ] Push `main` to `origin`.

## Self-Review

This plan covers the approved before/after chart cache, session-state snapshot behavior, comparison metadata, and crypto market expansion. No external APIs beyond the existing yfinance provider are added.
