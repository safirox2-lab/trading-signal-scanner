# Trading Signal Scanner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Streamlit trading scanner that reads market data, calculates transparent indicators, scores long/short opportunities, manages risk, and runs simple historical backtests.

**Architecture:** The app is split into small Python modules: models, indicators, strategy detection, risk/scoring, data providers, backtesting, and UI. The first data provider uses `yfinance`, but the scanner depends on a provider interface so live/broker providers can be added later.

**Tech Stack:** Python 3, Streamlit, Pandas, NumPy, yfinance, pytest.

---

## File Structure

- Create: `requirements.txt` with runtime and test dependencies.
- Create: `README.md` with local usage, limitations, and disclaimer.
- Create: `.gitignore` to keep virtualenvs, caches, and `.superpowers/` out of commits.
- Create: `app.py` as the Streamlit UI entrypoint.
- Create: `src/__init__.py` and package initializers.
- Create: `src/models/market.py` for OHLCV validation and symbol configuration.
- Create: `src/models/signals.py` for signal, trade plan, and score data structures.
- Create: `src/indicators/trend.py` for EMA and trend regime.
- Create: `src/indicators/momentum.py` for RSI and EMA cross helpers.
- Create: `src/indicators/volatility.py` for ATR.
- Create: `src/indicators/structure.py` for swing highs/lows and BOS/ChoCH.
- Create: `src/indicators/imbalance.py` for FVG detection.
- Create: `src/strategies/order_blocks.py` for order block candidates.
- Create: `src/strategies/liquidity.py` for equal highs/lows and sweep detection.
- Create: `src/risk/position_sizing.py` for 1 percent risk sizing.
- Create: `src/risk/trade_plan.py` for SL/TP and scoring.
- Create: `src/data/providers.py` for the provider protocol and symbol map.
- Create: `src/data/yfinance_provider.py` for the initial provider.
- Create: `src/strategies/scanner.py` to combine data, indicators, strategies, and risk into ranked opportunities.
- Create: `src/backtest/metrics.py` for drawdown, win rate, profit factor.
- Create: `src/backtest/engine.py` for chronological trade simulation.
- Create: tests under `tests/` matching the core modules.

## Task 1: Project Scaffold And Imports

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `README.md`
- Create: `src/__init__.py`
- Create: `src/data/__init__.py`
- Create: `src/indicators/__init__.py`
- Create: `src/strategies/__init__.py`
- Create: `src/risk/__init__.py`
- Create: `src/backtest/__init__.py`
- Create: `src/models/__init__.py`
- Create: `tests/test_project_imports.py`

- [ ] **Step 1: Initialize Git if needed**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' rev-parse --show-toplevel
```

Expected if not initialized: `fatal: not a git repository`.

Then run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' init
```

Expected: Git initializes a repository in `H:\Workspace\.git`.

- [ ] **Step 2: Create dependency and ignore files**

Write `.gitignore`:

```text
.venv/
__pycache__/
.pytest_cache/
.streamlit/secrets.toml
.superpowers/
*.pyc
*.pyo
```

Write `requirements.txt`:

```text
numpy>=1.26
pandas>=2.2
pytest>=8.0
streamlit>=1.35
yfinance>=0.2.40
```

Write `README.md`:

```markdown
# Trading Signal Scanner

Local Streamlit app for scanning liquid forex pairs, US index proxies, and gold proxies for technical long/short opportunities.

This is an educational analysis tool. It does not guarantee profit, does not provide financial advice, and does not execute trades.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```
```

- [ ] **Step 3: Create package initializers**

Write these files with a single docstring:

```python
"""Trading Signal Scanner package."""
```

Files:

```text
src/__init__.py
src/data/__init__.py
src/indicators/__init__.py
src/strategies/__init__.py
src/risk/__init__.py
src/backtest/__init__.py
src/models/__init__.py
```

- [ ] **Step 4: Write the import smoke test**

Write `tests/test_project_imports.py`:

```python
def test_package_imports():
    import src

    assert src.__doc__
```

- [ ] **Step 5: Run test to verify scaffold**

Run:

```powershell
python -m pytest tests/test_project_imports.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit scaffold**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add .gitignore README.md requirements.txt src tests
& 'C:\Program Files\Git\cmd\git.exe' commit -m "chore: scaffold trading scanner project"
```

Expected: commit succeeds.

## Task 2: Core Models And Market Configuration

**Files:**
- Create: `src/models/market.py`
- Create: `src/models/signals.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write model tests**

Write `tests/test_models.py`:

```python
import pandas as pd
import pytest

from src.models.market import MarketSymbol, validate_ohlcv
from src.models.signals import Direction, SignalCandidate, TradePlan


def test_validate_ohlcv_accepts_required_columns():
    df = pd.DataFrame(
        {
            "open": [1.0],
            "high": [1.2],
            "low": [0.9],
            "close": [1.1],
            "volume": [100],
        }
    )

    validated = validate_ohlcv(df)

    assert list(validated.columns) == ["open", "high", "low", "close", "volume"]


def test_validate_ohlcv_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing OHLCV columns"):
        validate_ohlcv(pd.DataFrame({"close": [1.0]}))


def test_signal_candidate_uses_direction_enum():
    signal = SignalCandidate(
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction=Direction.LONG,
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=("EMA", "OB"),
        reasons=("trend aligned",),
    )

    assert signal.direction.value == "LONG"
    assert signal.score == 80


def test_market_symbol_stores_provider_symbol():
    symbol = MarketSymbol(display="EUR/USD", provider_symbol="EURUSD=X", market="forex")

    assert symbol.provider_symbol == "EURUSD=X"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_models.py -v
```

Expected: FAIL with `ModuleNotFoundError` for `src.models.market`.

- [ ] **Step 3: Implement models**

Write `src/models/market.py`:

```python
from dataclasses import dataclass

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class MarketSymbol:
    display: str
    provider_symbol: str
    market: str


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(missing)}")

    result = normalized.loc[:, REQUIRED_OHLCV_COLUMNS].copy()
    for column in REQUIRED_OHLCV_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.dropna(subset=["open", "high", "low", "close"])
```

Write `src/models/signals.py`:

```python
from dataclasses import dataclass
from enum import Enum


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class TradePlan:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    position_size: float
    amount_at_risk: float


@dataclass(frozen=True)
class SignalCandidate:
    symbol: str
    display_symbol: str
    direction: Direction
    timeframe: str
    entry: float
    stop_loss: float
    take_profit: float
    score: int
    risk_reward: float
    strategy_tags: tuple[str, ...]
    reasons: tuple[str, ...]
```

- [ ] **Step 4: Run model tests**

Run:

```powershell
python -m pytest tests/test_models.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit models**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/models tests/test_models.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add market and signal models"
```

Expected: commit succeeds.

## Task 3: Technical Indicators

**Files:**
- Create: `src/indicators/trend.py`
- Create: `src/indicators/momentum.py`
- Create: `src/indicators/volatility.py`
- Test: `tests/test_indicators.py`

- [ ] **Step 1: Write indicator tests**

Write `tests/test_indicators.py`:

```python
import pandas as pd

from src.indicators.momentum import ema_cross_direction, rsi
from src.indicators.trend import ema, trend_regime
from src.indicators.volatility import atr


def test_ema_returns_series_same_length():
    series = pd.Series([1, 2, 3, 4, 5], dtype=float)

    result = ema(series, span=3)

    assert len(result) == 5
    assert result.iloc[-1] > result.iloc[0]


def test_trend_regime_bullish_when_fast_above_slow():
    df = pd.DataFrame({"close": list(range(1, 260))})

    result = trend_regime(df, fast_span=10, slow_span=30)

    assert result == "bullish"


def test_rsi_stays_between_zero_and_one_hundred():
    values = pd.Series([1, 2, 3, 2, 4, 5, 4, 6, 7, 6, 8, 9, 10, 9, 11], dtype=float)

    result = rsi(values, period=5).dropna()

    assert result.between(0, 100).all()


def test_ema_cross_direction_detects_long_cross():
    fast = pd.Series([1.0, 1.0, 3.0])
    slow = pd.Series([2.0, 2.0, 2.0])

    assert ema_cross_direction(fast, slow) == "long"


def test_atr_uses_true_range():
    df = pd.DataFrame(
        {
            "high": [10.0, 12.0, 13.0],
            "low": [8.0, 9.0, 10.0],
            "close": [9.0, 11.0, 12.0],
        }
    )

    result = atr(df, period=2)

    assert result.iloc[-1] > 0
```

- [ ] **Step 2: Run indicator tests to verify failure**

Run:

```powershell
python -m pytest tests/test_indicators.py -v
```

Expected: FAIL with missing indicator modules.

- [ ] **Step 3: Implement trend indicators**

Write `src/indicators/trend.py`:

```python
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    if span <= 0:
        raise ValueError("EMA span must be positive")
    return series.astype(float).ewm(span=span, adjust=False).mean()


def trend_regime(df: pd.DataFrame, fast_span: int = 50, slow_span: int = 200) -> str:
    close = df["close"].astype(float)
    if len(close) < slow_span:
        return "uncertain"
    fast = ema(close, fast_span).iloc[-1]
    slow = ema(close, slow_span).iloc[-1]
    price = close.iloc[-1]
    if price > slow and fast > slow:
        return "bullish"
    if price < slow and fast < slow:
        return "bearish"
    return "sideways"
```

- [ ] **Step 4: Implement momentum indicators**

Write `src/indicators/momentum.py`:

```python
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    if period <= 0:
        raise ValueError("RSI period must be positive")
    delta = series.astype(float).diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(period, min_periods=period).mean()
    avg_loss = losses.rolling(period, min_periods=period).mean()
    relative_strength = avg_gain / avg_loss.replace(0, pd.NA)
    result = 100 - (100 / (1 + relative_strength))
    return result.fillna(50).clip(0, 100)


def ema_cross_direction(fast: pd.Series, slow: pd.Series) -> str | None:
    if len(fast) < 2 or len(slow) < 2:
        return None
    previous_fast, current_fast = fast.iloc[-2], fast.iloc[-1]
    previous_slow, current_slow = slow.iloc[-2], slow.iloc[-1]
    if previous_fast <= previous_slow and current_fast > current_slow:
        return "long"
    if previous_fast >= previous_slow and current_fast < current_slow:
        return "short"
    return None
```

- [ ] **Step 5: Implement ATR**

Write `src/indicators/volatility.py`:

```python
import pandas as pd


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if period <= 0:
        raise ValueError("ATR period must be positive")
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    close = df["close"].astype(float)
    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.rolling(period, min_periods=1).mean()
```

- [ ] **Step 6: Run indicator tests**

Run:

```powershell
python -m pytest tests/test_indicators.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit indicators**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/indicators tests/test_indicators.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add transparent technical indicators"
```

Expected: commit succeeds.

## Task 4: Structure, Imbalance, Order Blocks, And Liquidity

**Files:**
- Create: `src/indicators/structure.py`
- Create: `src/indicators/imbalance.py`
- Create: `src/strategies/order_blocks.py`
- Create: `src/strategies/liquidity.py`
- Test: `tests/test_market_structure.py`

- [ ] **Step 1: Write structure tests**

Write `tests/test_market_structure.py`:

```python
import pandas as pd

from src.indicators.imbalance import fair_value_gaps
from src.indicators.structure import latest_structure_break, swing_points
from src.strategies.liquidity import liquidity_sweep
from src.strategies.order_blocks import order_block_candidates


def test_swing_points_marks_local_extremes():
    df = pd.DataFrame(
        {
            "high": [1, 3, 2, 4, 2],
            "low": [0, 1, 1, 1, 0],
            "close": [1, 2, 2, 3, 1],
        }
    )

    swings = swing_points(df, window=1)

    assert swings["swing_high"].sum() == 2


def test_latest_structure_break_detects_bullish_break():
    df = pd.DataFrame(
        {
            "high": [1, 3, 2, 2.5, 3.5],
            "low": [0.5, 1, 1, 1.5, 2],
            "close": [0.9, 2.5, 2.0, 2.2, 3.4],
        }
    )

    assert latest_structure_break(df, window=1) == "bullish_bos"


def test_fair_value_gap_detects_bullish_gap():
    df = pd.DataFrame(
        {
            "high": [10.0, 11.0, 13.0],
            "low": [9.0, 10.5, 12.0],
            "close": [9.5, 10.8, 12.5],
        }
    )

    gaps = fair_value_gaps(df)

    assert gaps.iloc[-1]["type"] == "bullish"


def test_order_block_candidate_detects_bullish_impulse():
    df = pd.DataFrame(
        {
            "open": [10.0, 9.8, 10.2, 11.5],
            "high": [10.1, 10.0, 11.0, 12.5],
            "low": [9.7, 9.5, 10.0, 11.0],
            "close": [9.8, 9.6, 10.9, 12.2],
            "volume": [100, 120, 200, 250],
        }
    )

    blocks = order_block_candidates(df, impulse_multiplier=1.2)

    assert blocks[-1]["direction"] == "long"


def test_liquidity_sweep_detects_rejection_above_equal_highs():
    df = pd.DataFrame(
        {
            "high": [10.0, 10.02, 10.5],
            "low": [9.5, 9.7, 9.8],
            "close": [9.8, 9.9, 9.95],
        }
    )

    assert liquidity_sweep(df, tolerance=0.05) == "bearish_sweep"
```

- [ ] **Step 2: Run structure tests to verify failure**

Run:

```powershell
python -m pytest tests/test_market_structure.py -v
```

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement swing and structure detection**

Write `src/indicators/structure.py`:

```python
import pandas as pd


def swing_points(df: pd.DataFrame, window: int = 2) -> pd.DataFrame:
    if window <= 0:
        raise ValueError("Swing window must be positive")
    highs = df["high"].astype(float)
    lows = df["low"].astype(float)
    result = pd.DataFrame(index=df.index)
    result["swing_high"] = False
    result["swing_low"] = False
    for index in range(window, len(df) - window):
        high_slice = highs.iloc[index - window : index + window + 1]
        low_slice = lows.iloc[index - window : index + window + 1]
        result.iloc[index, result.columns.get_loc("swing_high")] = highs.iloc[index] == high_slice.max()
        result.iloc[index, result.columns.get_loc("swing_low")] = lows.iloc[index] == low_slice.min()
    return result


def latest_structure_break(df: pd.DataFrame, window: int = 2) -> str | None:
    swings = swing_points(df, window=window)
    close = df["close"].astype(float)
    previous_swings = swings.iloc[:-1]
    swing_highs = df.loc[previous_swings["swing_high"], "high"]
    swing_lows = df.loc[previous_swings["swing_low"], "low"]
    if not swing_highs.empty and close.iloc[-1] > float(swing_highs.iloc[-1]):
        return "bullish_bos"
    if not swing_lows.empty and close.iloc[-1] < float(swing_lows.iloc[-1]):
        return "bearish_bos"
    return None
```

- [ ] **Step 4: Implement FVG detection**

Write `src/indicators/imbalance.py`:

```python
import pandas as pd


def fair_value_gaps(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str | None]] = []
    for index in range(len(df)):
        if index < 2:
            rows.append({"type": None, "lower": None, "upper": None})
            continue
        first = df.iloc[index - 2]
        third = df.iloc[index]
        if float(first["high"]) < float(third["low"]):
            rows.append({"type": "bullish", "lower": float(first["high"]), "upper": float(third["low"])})
        elif float(first["low"]) > float(third["high"]):
            rows.append({"type": "bearish", "lower": float(third["high"]), "upper": float(first["low"])})
        else:
            rows.append({"type": None, "lower": None, "upper": None})
    return pd.DataFrame(rows, index=df.index)
```

- [ ] **Step 5: Implement order block candidates**

Write `src/strategies/order_blocks.py`:

```python
import pandas as pd


def order_block_candidates(df: pd.DataFrame, impulse_multiplier: float = 1.5) -> list[dict[str, float | int | str]]:
    if len(df) < 3:
        return []
    ranges = (df["high"].astype(float) - df["low"].astype(float)).rolling(3, min_periods=1).mean()
    blocks: list[dict[str, float | int | str]] = []
    for index in range(1, len(df)):
        previous = df.iloc[index - 1]
        current = df.iloc[index]
        current_range = float(current["high"] - current["low"])
        average_range = float(ranges.iloc[index - 1])
        if average_range <= 0 or current_range < average_range * impulse_multiplier:
            continue
        previous_bearish = float(previous["close"]) < float(previous["open"])
        previous_bullish = float(previous["close"]) > float(previous["open"])
        current_bullish = float(current["close"]) > float(current["open"])
        current_bearish = float(current["close"]) < float(current["open"])
        if previous_bearish and current_bullish:
            blocks.append(
                {
                    "index": index - 1,
                    "direction": "long",
                    "low": float(previous["low"]),
                    "high": float(previous["high"]),
                    "mid": float((previous["open"] + previous["close"]) / 2),
                }
            )
        if previous_bullish and current_bearish:
            blocks.append(
                {
                    "index": index - 1,
                    "direction": "short",
                    "low": float(previous["low"]),
                    "high": float(previous["high"]),
                    "mid": float((previous["open"] + previous["close"]) / 2),
                }
            )
    return blocks
```

- [ ] **Step 6: Implement liquidity sweeps**

Write `src/strategies/liquidity.py`:

```python
import pandas as pd


def liquidity_sweep(df: pd.DataFrame, tolerance: float = 0.001) -> str | None:
    if len(df) < 3:
        return None
    prior = df.iloc[-3:-1]
    current = df.iloc[-1]
    equal_high = abs(float(prior["high"].iloc[0]) - float(prior["high"].iloc[1])) <= tolerance
    equal_low = abs(float(prior["low"].iloc[0]) - float(prior["low"].iloc[1])) <= tolerance
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    if equal_high and float(current["high"]) > prior_high and float(current["close"]) < prior_high:
        return "bearish_sweep"
    if equal_low and float(current["low"]) < prior_low and float(current["close"]) > prior_low:
        return "bullish_sweep"
    return None
```

- [ ] **Step 7: Run structure tests**

Run:

```powershell
python -m pytest tests/test_market_structure.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit structure modules**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/indicators/structure.py src/indicators/imbalance.py src/strategies/order_blocks.py src/strategies/liquidity.py tests/test_market_structure.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: detect structure imbalances and liquidity"
```

Expected: commit succeeds.

## Task 5: Risk, Trade Plans, And Opportunity Scoring

**Files:**
- Create: `src/risk/position_sizing.py`
- Create: `src/risk/trade_plan.py`
- Test: `tests/test_risk_and_scoring.py`

- [ ] **Step 1: Write risk and scoring tests**

Write `tests/test_risk_and_scoring.py`:

```python
from src.models.signals import Direction
from src.risk.position_sizing import position_size
from src.risk.trade_plan import build_trade_plan, score_signal


def test_position_size_risks_one_percent():
    result = position_size(account_balance=10_000, risk_percent=1, entry=100, stop_loss=95)

    assert result.amount_at_risk == 100
    assert result.units == 20


def test_build_trade_plan_long_uses_two_r_target():
    plan = build_trade_plan(Direction.LONG, account_balance=10_000, entry=100, stop_loss=95)

    assert plan.take_profit == 110
    assert plan.risk_reward == 2


def test_build_trade_plan_short_uses_two_r_target():
    plan = build_trade_plan(Direction.SHORT, account_balance=10_000, entry=100, stop_loss=105)

    assert plan.take_profit == 90
    assert plan.risk_reward == 2


def test_score_signal_caps_at_one_hundred():
    score, reasons = score_signal(
        trend_aligned=True,
        valid_order_block=True,
        structure_break=True,
        fvg=True,
        liquidity_sweep=True,
        ema_momentum=True,
        risk_reward_ok=True,
        atr_rsi_quality=True,
    )

    assert score == 100
    assert "trend aligned" in reasons
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
python -m pytest tests/test_risk_and_scoring.py -v
```

Expected: FAIL with missing modules.

- [ ] **Step 3: Implement position sizing**

Write `src/risk/position_sizing.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSize:
    units: float
    amount_at_risk: float
    stop_distance: float


def position_size(account_balance: float, risk_percent: float, entry: float, stop_loss: float) -> PositionSize:
    if account_balance <= 0:
        raise ValueError("Account balance must be positive")
    if risk_percent <= 0:
        raise ValueError("Risk percent must be positive")
    stop_distance = abs(float(entry) - float(stop_loss))
    if stop_distance <= 0:
        raise ValueError("Stop distance must be positive")
    amount_at_risk = float(account_balance) * (float(risk_percent) / 100)
    return PositionSize(units=amount_at_risk / stop_distance, amount_at_risk=amount_at_risk, stop_distance=stop_distance)
```

- [ ] **Step 4: Implement trade plan and scoring**

Write `src/risk/trade_plan.py`:

```python
from src.models.signals import Direction, TradePlan
from src.risk.position_sizing import position_size


def build_trade_plan(
    direction: Direction,
    account_balance: float,
    entry: float,
    stop_loss: float,
    risk_percent: float = 1.0,
    reward_multiple: float = 2.0,
) -> TradePlan:
    size = position_size(account_balance, risk_percent, entry, stop_loss)
    risk_distance = abs(entry - stop_loss)
    if direction == Direction.LONG:
        take_profit = entry + (risk_distance * reward_multiple)
    else:
        take_profit = entry - (risk_distance * reward_multiple)
    return TradePlan(
        entry=float(entry),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        risk_reward=float(reward_multiple),
        position_size=float(size.units),
        amount_at_risk=float(size.amount_at_risk),
    )


def score_signal(
    *,
    trend_aligned: bool,
    valid_order_block: bool,
    structure_break: bool,
    fvg: bool,
    liquidity_sweep: bool,
    ema_momentum: bool,
    risk_reward_ok: bool,
    atr_rsi_quality: bool,
) -> tuple[int, tuple[str, ...]]:
    weights = (
        (trend_aligned, 20, "trend aligned"),
        (valid_order_block, 20, "valid order block"),
        (structure_break, 15, "structure break"),
        (fvg, 10, "fair value gap"),
        (liquidity_sweep, 10, "liquidity sweep"),
        (ema_momentum, 10, "EMA momentum"),
        (risk_reward_ok, 10, "risk/reward >= 1:2"),
        (atr_rsi_quality, 5, "ATR/RSI quality"),
    )
    score = sum(points for enabled, points, _reason in weights if enabled)
    reasons = tuple(reason for enabled, _points, reason in weights if enabled)
    return min(100, score), reasons
```

- [ ] **Step 5: Run risk tests**

Run:

```powershell
python -m pytest tests/test_risk_and_scoring.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit risk and scoring**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/risk tests/test_risk_and_scoring.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add risk sizing and scoring"
```

Expected: commit succeeds.

## Task 6: Data Provider And Scanner

**Files:**
- Create: `src/data/providers.py`
- Create: `src/data/yfinance_provider.py`
- Create: `src/strategies/scanner.py`
- Test: `tests/test_scanner.py`

- [ ] **Step 1: Write scanner tests with in-memory provider**

Write `tests/test_scanner.py`:

```python
import pandas as pd

from src.data.providers import MarketDataProvider, default_symbols
from src.strategies.scanner import scan_symbol


class StaticProvider(MarketDataProvider):
    def history(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        rows = []
        price = 100.0
        for index in range(260):
            open_price = price
            close_price = price + 0.2
            rows.append(
                {
                    "open": open_price,
                    "high": close_price + 0.5,
                    "low": open_price - 0.5,
                    "close": close_price,
                    "volume": 1000 + index,
                }
            )
            price = close_price
        return pd.DataFrame(rows)


def test_default_symbols_include_liquid_markets():
    symbols = default_symbols()

    assert any(symbol.display == "EUR/USD" for symbol in symbols)
    assert any(symbol.market == "indices" for symbol in symbols)


def test_scan_symbol_returns_signal_with_risk_fields():
    signal = scan_symbol(
        provider=StaticProvider(),
        display_symbol="TEST",
        provider_symbol="TEST",
        timeframe="1h",
        account_balance=10_000,
        min_score=0,
    )

    assert signal is not None
    assert signal.stop_loss != signal.entry
    assert signal.take_profit != signal.entry
```

- [ ] **Step 2: Run scanner tests to verify failure**

Run:

```powershell
python -m pytest tests/test_scanner.py -v
```

Expected: FAIL with missing provider and scanner modules.

- [ ] **Step 3: Implement provider protocol and symbols**

Write `src/data/providers.py`:

```python
from typing import Protocol

import pandas as pd

from src.models.market import MarketSymbol


class MarketDataProvider(Protocol):
    def history(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        raise NotImplementedError


def default_symbols() -> tuple[MarketSymbol, ...]:
    return (
        MarketSymbol("EUR/USD", "EURUSD=X", "forex"),
        MarketSymbol("GBP/USD", "GBPUSD=X", "forex"),
        MarketSymbol("USD/JPY", "JPY=X", "forex"),
        MarketSymbol("AUD/USD", "AUDUSD=X", "forex"),
        MarketSymbol("USD/CAD", "CAD=X", "forex"),
        MarketSymbol("S&P 500", "^GSPC", "indices"),
        MarketSymbol("NASDAQ 100", "^NDX", "indices"),
        MarketSymbol("Dow Jones", "^DJI", "indices"),
        MarketSymbol("Gold", "GC=F", "commodities"),
    )
```

- [ ] **Step 4: Implement yfinance provider**

Write `src/data/yfinance_provider.py`:

```python
import pandas as pd
import yfinance as yf

from src.models.market import validate_ohlcv


class YFinanceProvider:
    def history(self, symbol: str, period: str = "6mo", interval: str = "1h") -> pd.DataFrame:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
        if df.empty:
            raise ValueError(f"No market data returned for {symbol}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [column[0] for column in df.columns]
        renamed = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        return validate_ohlcv(renamed)
```

- [ ] **Step 5: Implement scanner**

Write `src/strategies/scanner.py`:

```python
from src.indicators.imbalance import fair_value_gaps
from src.indicators.momentum import ema_cross_direction, rsi
from src.indicators.trend import ema, trend_regime
from src.indicators.volatility import atr
from src.models.market import validate_ohlcv
from src.models.signals import Direction, SignalCandidate
from src.risk.trade_plan import build_trade_plan, score_signal
from src.strategies.liquidity import liquidity_sweep
from src.strategies.order_blocks import order_block_candidates


def scan_symbol(
    provider,
    display_symbol: str,
    provider_symbol: str,
    timeframe: str,
    account_balance: float,
    min_score: int = 70,
    period: str = "6mo",
) -> SignalCandidate | None:
    df = validate_ohlcv(provider.history(provider_symbol, period=period, interval=timeframe))
    if len(df) < 60:
        return None
    regime = trend_regime(df, fast_span=20, slow_span=50)
    close = df["close"]
    fast = ema(close, 9)
    slow = ema(close, 21)
    cross = ema_cross_direction(fast, slow)
    blocks = order_block_candidates(df)
    latest_block = blocks[-1] if blocks else None
    gaps = fair_value_gaps(df)
    latest_gap = gaps.iloc[-1]
    sweep = liquidity_sweep(df)
    latest_atr = float(atr(df).iloc[-1])
    latest_rsi = float(rsi(close).iloc[-1])

    direction = Direction.LONG if regime == "bullish" else Direction.SHORT if regime == "bearish" else Direction.LONG
    if latest_block and latest_block["direction"] == "short":
        direction = Direction.SHORT

    entry = float(close.iloc[-1])
    if direction == Direction.LONG:
        stop_loss = min(entry - latest_atr, float(latest_block["low"]) if latest_block else entry - latest_atr)
    else:
        stop_loss = max(entry + latest_atr, float(latest_block["high"]) if latest_block else entry + latest_atr)
    plan = build_trade_plan(direction, account_balance, entry, stop_loss)

    trend_aligned = (direction == Direction.LONG and regime == "bullish") or (direction == Direction.SHORT and regime == "bearish")
    score, reasons = score_signal(
        trend_aligned=trend_aligned,
        valid_order_block=latest_block is not None,
        structure_break=True,
        fvg=latest_gap["type"] is not None,
        liquidity_sweep=sweep is not None,
        ema_momentum=(cross == "long" and direction == Direction.LONG) or (cross == "short" and direction == Direction.SHORT),
        risk_reward_ok=plan.risk_reward >= 2,
        atr_rsi_quality=latest_atr > 0 and 20 < latest_rsi < 80,
    )
    if score < min_score:
        return None
    tags = tuple(reason.upper() for reason in reasons[:4])
    return SignalCandidate(
        symbol=provider_symbol,
        display_symbol=display_symbol,
        direction=direction,
        timeframe=timeframe,
        entry=round(plan.entry, 5),
        stop_loss=round(plan.stop_loss, 5),
        take_profit=round(plan.take_profit, 5),
        score=score,
        risk_reward=plan.risk_reward,
        strategy_tags=tags,
        reasons=reasons,
    )
```

- [ ] **Step 6: Run scanner tests**

Run:

```powershell
python -m pytest tests/test_scanner.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit provider and scanner**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/data src/strategies/scanner.py tests/test_scanner.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add market data provider and scanner"
```

Expected: commit succeeds.

## Task 7: Backtest Engine And Metrics

**Files:**
- Create: `src/backtest/metrics.py`
- Create: `src/backtest/engine.py`
- Test: `tests/test_backtest.py`

- [ ] **Step 1: Write backtest tests**

Write `tests/test_backtest.py`:

```python
import pandas as pd

from src.backtest.engine import backtest_static_plan
from src.backtest.metrics import max_drawdown, summarize_trades
from src.models.signals import Direction


def test_max_drawdown_detects_drop_from_peak():
    assert max_drawdown([100, 120, 90, 130]) == 0.25


def test_summarize_trades_calculates_win_rate():
    summary = summarize_trades([2.0, -1.0, 2.0])

    assert summary["trades"] == 3
    assert round(summary["win_rate"], 2) == 66.67
    assert summary["profit_factor"] == 4.0


def test_backtest_static_plan_closes_at_take_profit():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [101, 111, 112],
            "low": [99, 100, 101],
            "close": [100, 110, 111],
            "volume": [1000, 1000, 1000],
        }
    )

    result = backtest_static_plan(df, Direction.LONG, entry=100, stop_loss=95, take_profit=110, initial_balance=10_000)

    assert result["final_balance"] > 10_000
    assert result["trades"] == 1
```

- [ ] **Step 2: Run backtest tests to verify failure**

Run:

```powershell
python -m pytest tests/test_backtest.py -v
```

Expected: FAIL with missing backtest modules.

- [ ] **Step 3: Implement metrics**

Write `src/backtest/metrics.py`:

```python
def max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return round(worst, 4)


def summarize_trades(r_multiples: list[float]) -> dict[str, float]:
    trades = len(r_multiples)
    wins = [value for value in r_multiples if value > 0]
    losses = [value for value in r_multiples if value < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "trades": trades,
        "win_rate": round((len(wins) / trades) * 100, 2) if trades else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
        "average_r": round(sum(r_multiples) / trades, 2) if trades else 0.0,
    }
```

- [ ] **Step 4: Implement backtest engine**

Write `src/backtest/engine.py`:

```python
import pandas as pd

from src.backtest.metrics import max_drawdown, summarize_trades
from src.models.signals import Direction


def backtest_static_plan(
    df: pd.DataFrame,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
    initial_balance: float,
    risk_percent: float = 1.0,
) -> dict[str, float]:
    risk_amount = initial_balance * (risk_percent / 100)
    risk_distance = abs(entry - stop_loss)
    if risk_distance <= 0:
        raise ValueError("Risk distance must be positive")
    equity = [initial_balance]
    r_multiples: list[float] = []
    for _, candle in df.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if direction == Direction.LONG:
            if low <= stop_loss:
                r_multiples.append(-1.0)
                equity.append(equity[-1] - risk_amount)
                break
            if high >= take_profit:
                reward = abs(take_profit - entry) / risk_distance
                r_multiples.append(reward)
                equity.append(equity[-1] + (risk_amount * reward))
                break
        else:
            if high >= stop_loss:
                r_multiples.append(-1.0)
                equity.append(equity[-1] - risk_amount)
                break
            if low <= take_profit:
                reward = abs(entry - take_profit) / risk_distance
                r_multiples.append(reward)
                equity.append(equity[-1] + (risk_amount * reward))
                break
    summary = summarize_trades(r_multiples)
    summary["initial_balance"] = initial_balance
    summary["final_balance"] = round(equity[-1], 2)
    summary["max_drawdown"] = max_drawdown(equity)
    return summary
```

- [ ] **Step 5: Run backtest tests**

Run:

```powershell
python -m pytest tests/test_backtest.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit backtesting**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/backtest tests/test_backtest.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add simple backtest engine"
```

Expected: commit succeeds.

## Task 8: Streamlit Dark Orange Interface

**Files:**
- Create: `app.py`
- Test: `tests/test_app_config.py`

- [ ] **Step 1: Write app configuration test**

Write `tests/test_app_config.py`:

```python
from app import APP_TITLE, THEME_ACCENT


def test_app_uses_dark_orange_identity():
    assert APP_TITLE == "Trading Signal Scanner"
    assert THEME_ACCENT == "#f97316"
```

- [ ] **Step 2: Run app test to verify failure**

Run:

```powershell
python -m pytest tests/test_app_config.py -v
```

Expected: FAIL because `app.py` does not exist.

- [ ] **Step 3: Implement Streamlit app**

Write `app.py`:

```python
import pandas as pd
import streamlit as st

from src.data.providers import default_symbols
from src.data.yfinance_provider import YFinanceProvider
from src.strategies.scanner import scan_symbol


APP_TITLE = "Trading Signal Scanner"
THEME_ACCENT = "#f97316"


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #0f1117; color: #f3f4f6; }
        [data-testid="stSidebar"] { background: #151923; }
        h1, h2, h3 { color: #f97316; }
        div[data-testid="stMetricValue"] { color: #fb923c; }
        .signal-card {
            background: #151923;
            border: 1px solid #272b35;
            border-radius: 8px;
            padding: 14px;
        }
        .disclaimer {
            color: #d1d5db;
            background: #1f2530;
            border-left: 4px solid #f97316;
            padding: 10px 12px;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def signals_to_frame(signals) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Symbol": signal.display_symbol,
                "Direction": signal.direction.value,
                "Score": signal.score,
                "Entry": signal.entry,
                "Stop Loss": signal.stop_loss,
                "Take Profit": signal.take_profit,
                "R:R": signal.risk_reward,
                "Timeframe": signal.timeframe,
                "Strategy": ", ".join(signal.strategy_tags),
            }
            for signal in signals
        ]
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_theme()
    st.title(APP_TITLE)
    st.markdown(
        '<div class="disclaimer">Herramienta educativa/de analisis. No es asesoria financiera ni garantia de ganancia.</div>',
        unsafe_allow_html=True,
    )

    provider = YFinanceProvider()
    symbols = default_symbols()

    with st.sidebar:
        st.header("Filtros")
        selected_markets = st.multiselect(
            "Mercados",
            sorted({symbol.market for symbol in symbols}),
            default=["forex", "indices", "commodities"],
        )
        timeframe = st.selectbox("Timeframe", ["1h", "1d"], index=0)
        min_score = st.slider("Score minimo", min_value=0, max_value=100, value=70, step=5)
        account_balance = st.number_input("Capital de cuenta", min_value=100.0, value=10_000.0, step=100.0)

    selected_symbols = [symbol for symbol in symbols if symbol.market in selected_markets]
    signals = []
    errors = []
    for symbol in selected_symbols:
        try:
            signal = scan_symbol(
                provider=provider,
                display_symbol=symbol.display,
                provider_symbol=symbol.provider_symbol,
                timeframe=timeframe,
                account_balance=account_balance,
                min_score=min_score,
            )
            if signal:
                signals.append(signal)
        except Exception as exc:
            errors.append(f"{symbol.display}: {exc}")

    signals = sorted(signals, key=lambda item: item.score, reverse=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Senales", len(signals))
    col2.metric("Score minimo", f"{min_score}%")
    col3.metric("Riesgo", "1%")
    col4.metric("Mercados", len(selected_symbols))

    st.subheader("Oportunidades")
    if signals:
        st.dataframe(signals_to_frame(signals), use_container_width=True, hide_index=True)
        selected = st.selectbox("Detalle de senal", [signal.display_symbol for signal in signals])
        signal = next(item for item in signals if item.display_symbol == selected)
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        st.write("Razones:", ", ".join(signal.reasons))
        st.write(f"Entrada: {signal.entry} | SL: {signal.stop_loss} | TP: {signal.take_profit}")
        st.write(f"Direccion: {signal.direction.value} | Score: {signal.score}% | R:R: {signal.risk_reward}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay oportunidades que superen el filtro actual.")

    if errors:
        with st.expander("Errores de datos"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run app config test**

Run:

```powershell
python -m pytest tests/test_app_config.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit Streamlit app**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app.py tests/test_app_config.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add dark orange Streamlit interface"
```

Expected: commit succeeds.

## Task 9: Full Verification And Local Run

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Install dependencies**

Run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Expected: dependencies install successfully.

- [ ] **Step 2: Run the full test suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 3: Start the local app**

Run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Expected: Streamlit prints a local URL, usually `http://localhost:8501`.

- [ ] **Step 4: Verify UI manually**

Open the Streamlit URL and confirm:

- Dark background is visible.
- Orange accents appear on headings, metrics, and active indicators.
- Opportunities table renders or a clear empty-state message appears.
- Data provider errors show as warnings, not stack traces.
- Every displayed signal has entry, stop loss, take profit, score, and risk/reward.

- [ ] **Step 5: Update README with verified URL and limitations**

Append to `README.md`:

```markdown
## Data Limitations

The first version uses yfinance for convenient market data access. Data can be delayed, incomplete, or unavailable for some symbols and intervals. Use the output for research and paper trading validation before risking capital.

## Verified Local Start

Run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open the local URL printed by Streamlit.
```

- [ ] **Step 6: Commit verification docs**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add README.md
& 'C:\Program Files\Git\cmd\git.exe' commit -m "docs: add data limitations and run notes"
```

Expected: commit succeeds.

## Self-Review

Spec coverage:

- Layered provider architecture is covered by Tasks 6 and 8.
- Liquid initial markets are covered by Task 6.
- Transparent indicators are covered by Task 3.
- Order blocks, FVG, BOS, and liquidity sweeps are covered by Task 4.
- Risk management, 1 percent position sizing, and 1:2 targets are covered by Task 5.
- Backtesting metrics are covered by Task 7.
- Dark orange Streamlit interface is covered by Task 8.
- Error handling and data limitations are covered by Tasks 6, 8, and 9.

No placeholders are intentionally left in this plan. The initial implementation is deliberately conservative and avoids automatic execution, machine learning, and TradingView scraping.
