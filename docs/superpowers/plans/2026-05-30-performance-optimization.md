# Performance Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve historical evaluation performance and remove Streamlit width deprecation warnings without changing trading semantics.

**Architecture:** Keep the existing Streamlit flow and public evaluation API. Optimize `src/evaluation/historical.py` by replacing repeated Pandas slicing and `iterrows()` paths with precomputed Series/array logic. Update `app.py` rendering calls to the current Streamlit `width="stretch"` API.

**Tech Stack:** Python 3.11, pandas, NumPy through pandas, Streamlit, pytest, compileall.

---

## File Structure

- Modify `src/evaluation/historical.py`: optimize trade outcome scanning, EMA cross index detection, FVG index extraction, liquidity sweep index detection, and evaluation loops.
- Modify `tests/test_historical_evaluation.py`: add regression tests that lock same-candle SL-first behavior for long and short trades and verify optimized profile detection still returns expected profile names.
- Modify `app.py`: replace deprecated `use_container_width=True` arguments with `width="stretch"` on Streamlit dataframe and Plotly chart calls.
- No database, provider, model, or journal schema changes.

## Task 1: Protect Historical Evaluation Semantics

**Files:**
- Modify: `tests/test_historical_evaluation.py`
- Test: `tests/test_historical_evaluation.py`

- [ ] **Step 1: Add regression tests**

Add these tests after `test_simulate_trade_outcome_counts_same_candle_touch_as_loss`:

```python
def test_simulate_trade_outcome_counts_short_same_candle_touch_as_loss():
    future = pd.DataFrame({"high": [106.0], "low": [88.0]})

    result = simulate_trade_outcome(future, Direction.SHORT, entry=100.0, stop_loss=105.0, take_profit=90.0)

    assert result == -1.0


def test_evaluate_strategy_profiles_returns_all_profiles_after_optimization():
    df = pd.DataFrame(
        {
            "open": [100, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112] * 8,
            "high": [102, 104, 105, 103, 107, 108, 106, 110, 111, 109, 114, 115] * 8,
            "low": [99, 100, 102, 100, 103, 104, 102, 106, 108, 105, 109, 111] * 8,
            "close": [101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 114] * 8,
            "volume": [1000, 1200, 900, 1500, 2000, 1000, 2500, 1100, 1300, 2600, 1400, 2800] * 8,
        }
    )

    evaluations = evaluate_strategy_profiles(df, Direction.LONG)

    assert [item.profile for item in evaluations] == [
        "Scalping / EMA Momentum",
        "Order Block",
        "FVG / Imbalance",
        "Liquidity Sweep",
        "Trend Alignment",
    ]
```

- [ ] **Step 2: Run the focused tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_historical_evaluation.py -q
```

Expected: all historical evaluation tests pass before optimization, confirming the new tests describe existing behavior.

- [ ] **Step 3: Commit tests**

Run:

```powershell
git add tests/test_historical_evaluation.py
git commit -m "test: protect historical evaluation semantics"
```

Expected: commit succeeds with only `tests/test_historical_evaluation.py`.

## Task 2: Optimize Historical Evaluation

**Files:**
- Modify: `src/evaluation/historical.py`
- Test: `tests/test_historical_evaluation.py`

- [ ] **Step 1: Replace row-based trade scanning with array-based scanning**

In `src/evaluation/historical.py`, add this helper above `simulate_trade_outcome`:

```python
def _trade_outcome_from_arrays(
    highs,
    lows,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
) -> float | None:
    risk = abs(entry - stop_loss)
    if risk <= 0:
        return None
    for high, low in zip(highs, lows):
        high_value = float(high)
        low_value = float(low)
        if direction == Direction.LONG:
            stop_hit = low_value <= stop_loss
            target_hit = high_value >= take_profit
        else:
            stop_hit = high_value >= stop_loss
            target_hit = low_value <= take_profit
        if stop_hit:
            return -1.0
        if target_hit:
            return round(abs(take_profit - entry) / risk, 2)
    return None
```

Then rewrite `simulate_trade_outcome` to delegate:

```python
def simulate_trade_outcome(
    future: pd.DataFrame,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
) -> float | None:
    return _trade_outcome_from_arrays(
        future["high"].to_numpy(),
        future["low"].to_numpy(),
        direction,
        entry,
        stop_loss,
        take_profit,
    )
```

- [ ] **Step 2: Optimize the evaluation loop**

Inside `evaluate_strategy_profiles`, create arrays once before the profile loop:

```python
close_values = df["close"].astype(float).to_numpy()
high_values = df["high"].astype(float).to_numpy()
low_values = df["low"].astype(float).to_numpy()
atr_values = atr(df, period=14).astype(float).to_numpy()
```

Then replace DataFrame `.iloc` reads and `df.iloc[index + 1 :]` calls inside the loop with array reads:

```python
entry = float(close_values[index])
atr_value = float(atr_values[index])
candle_range = float(high_values[index] - low_values[index])
distance = max(atr_value * config.atr_stop_multiple, candle_range, entry * 0.001)
if direction == Direction.LONG:
    stop_loss = entry - distance
    take_profit = entry + (distance * config.reward_multiple)
else:
    stop_loss = entry + distance
    take_profit = entry - (distance * config.reward_multiple)
outcome = _trade_outcome_from_arrays(
    high_values[index + 1 :],
    low_values[index + 1 :],
    direction,
    entry,
    stop_loss,
    take_profit,
)
```

- [ ] **Step 3: Optimize profile index helpers**

Remove the unused import of `ema_cross_direction` and `liquidity_sweep` from `src/evaluation/historical.py`.

Replace `_ema_momentum_indexes` with:

```python
def _ema_momentum_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    fast = ema(df["close"], 9)
    slow = ema(df["close"], 21)
    if direction == Direction.LONG:
        crosses = (fast.shift(1) <= slow.shift(1)) & (fast > slow)
    else:
        crosses = (fast.shift(1) >= slow.shift(1)) & (fast < slow)
    return [int(index) for index in crosses[crosses].index.to_series().map(df.index.get_loc) if index < len(df) - 1]
```

Replace `_fvg_indexes` with:

```python
def _fvg_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "bullish" if direction == Direction.LONG else "bearish"
    gaps = fair_value_gaps(df)
    matches = gaps["type"].eq(wanted)
    return [int(index) for index in matches[matches].index.to_series().map(gaps.index.get_loc) if index < len(df) - 1]
```

Replace `_liquidity_sweep_indexes` with:

```python
def _liquidity_sweep_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    previous_high = high.shift(1)
    older_high = high.shift(2)
    previous_low = low.shift(1)
    older_low = low.shift(2)

    equal_high = (older_high - previous_high).abs() <= 0.05
    equal_low = (older_low - previous_low).abs() <= 0.05
    prior_high = pd.concat([older_high, previous_high], axis=1).max(axis=1)
    prior_low = pd.concat([older_low, previous_low], axis=1).min(axis=1)

    if direction == Direction.LONG:
        matches = equal_low & (low < prior_low) & (close > prior_low)
    else:
        matches = equal_high & (high > prior_high) & (close < prior_high)
    return [int(index) for index in matches[matches].index.to_series().map(df.index.get_loc) if 2 <= index < len(df) - 1]
```

- [ ] **Step 4: Run historical tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_historical_evaluation.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Run synthetic timing check**

Run:

```powershell
.\.venv\Scripts\python.exe -c "import time, pandas as pd, numpy as np; from src.evaluation.historical import evaluate_strategy_profiles; from src.models.signals import Direction; n=5000; idx=pd.date_range('2020-01-01', periods=n, freq='h'); base=np.linspace(100,150,n)+np.sin(np.arange(n)/10)*2; df=pd.DataFrame({'open':base,'high':base+1,'low':base-1,'close':base+np.sin(np.arange(n)/5),'volume':np.ones(n)*1000}, index=idx); t=time.perf_counter(); r=evaluate_strategy_profiles(df, Direction.LONG); print('evaluate_strategy_profiles_5000_rows_seconds=', round(time.perf_counter()-t, 4)); print([(x.profile, x.setups) for x in r])"
```

Expected: runtime is materially below the previously measured `12.295` seconds while returning five profile rows.

- [ ] **Step 6: Commit optimization**

Run:

```powershell
git add src/evaluation/historical.py tests/test_historical_evaluation.py
git commit -m "perf: optimize historical strategy evaluation"
```

Expected: commit succeeds with historical evaluation code and tests.

## Task 3: Update Streamlit Width Arguments

**Files:**
- Modify: `app.py`
- Test: `tests/test_app_config.py`

- [ ] **Step 1: Replace deprecated width arguments**

In `app.py`, replace every:

```python
use_container_width=True
```

with:

```python
width="stretch"
```

This applies to `st.dataframe(...)` and `st.plotly_chart(...)` calls.

- [ ] **Step 2: Confirm no deprecated calls remain**

Run:

```powershell
rg -n "use_container_width" app.py
```

Expected: no matches and exit code 1 from `rg`.

- [ ] **Step 3: Run app helper tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_app_config.py -q
```

Expected: all app config tests pass.

- [ ] **Step 4: Commit Streamlit compatibility update**

Run:

```powershell
git add app.py
git commit -m "chore: update streamlit width arguments"
```

Expected: commit succeeds with only `app.py`.

## Task 4: Full Verification

**Files:**
- Modify: none unless verification reveals a defect.
- Test: full project.

- [ ] **Step 1: Run full test suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: `71` or more tests pass, with zero failures.

- [ ] **Step 2: Compile project**

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py src
```

Expected: exit code 0.

- [ ] **Step 3: Run final timing check**

Run the same synthetic timing command from Task 2 Step 5.

Expected: output includes `evaluate_strategy_profiles_5000_rows_seconds=` with a value materially below `12.295`.

- [ ] **Step 4: Review diff and status**

Run:

```powershell
git status --short
git log --oneline -3
```

Expected: no uncommitted code changes unless verification fixes were needed; recent commits show the optimization and compatibility work.

## Self-Review

Spec coverage:

- Historical evaluation performance: Task 2.
- Same-candle SL-first semantics: Task 1 and Task 2.
- Streamlit compatibility warnings: Task 3.
- No strategy, database, provider, or journal behavior changes: file structure and task scopes avoid those areas.
- Verification evidence: Task 4.

Placeholder scan: no placeholder tokens, undefined helper names, or vague test instructions remain.

Type consistency: new helper `_trade_outcome_from_arrays` accepts high/low arrays plus existing `Direction` and float trade levels, and is called only from `simulate_trade_outcome` and `evaluate_strategy_profiles`.
