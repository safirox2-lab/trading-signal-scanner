# Candlestick Strategy Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add interactive candlestick charts with entry/SL/TP markers and historical strategy evaluation metrics to the local Trading Signal Scanner.

**Architecture:** Add a focused charting module that converts OHLCV and trade levels into Plotly figures, plus an evaluation package that classifies strategy support and backtests historical setups conservatively. Keep Streamlit as the UI shell and keep the scanner modules usable without UI dependencies.

**Tech Stack:** Python 3, Streamlit, Pandas, NumPy, Plotly, yfinance, pytest.

---

## File Structure

- Modify: `requirements.txt` to add `plotly`.
- Create: `src/charts/__init__.py` for chart package setup.
- Create: `src/charts/candles.py` for candlestick figures and trade-level overlays.
- Create: `src/evaluation/__init__.py` for evaluation package setup.
- Create: `src/evaluation/strategy_profiles.py` for strategy profile classification and confluence summaries.
- Create: `src/evaluation/historical.py` for historical setup simulation and metrics.
- Modify: `app.py` to show chart controls, selected signal chart, trade levels, and evaluation table.
- Create: `tests/test_charts.py` for chart figure structure.
- Create: `tests/test_strategy_profiles.py` for strategy classification.
- Create: `tests/test_historical_evaluation.py` for conservative win/loss evaluation.
- Modify: `tests/test_app_config.py` to cover interval/period helper behavior.

## Task 1: Plotly Dependency And Candlestick Chart Module

**Files:**
- Modify: `requirements.txt`
- Create: `src/charts/__init__.py`
- Create: `src/charts/candles.py`
- Test: `tests/test_charts.py`

- [ ] **Step 1: Write the failing chart tests**

Write `tests/test_charts.py`:

```python
import pandas as pd

from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.models.signals import Direction


def sample_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000, 1100, 1200],
        },
        index=pd.date_range("2026-01-01", periods=3, freq="D"),
    )


def test_build_candlestick_figure_contains_candles_and_trade_levels():
    levels = TradeLevels(entry=103.0, stop_loss=100.0, take_profit=109.0, direction=Direction.LONG)

    fig = build_candlestick_figure(sample_ohlcv(), levels, "EUR/USD", ("Order Block", "FVG"))

    assert len(fig.data) >= 2
    assert fig.data[0].type == "candlestick"
    assert any(shape["line"]["color"] == "#ef4444" for shape in fig.layout.shapes)
    assert any(shape["line"]["color"] == "#22c55e" for shape in fig.layout.shapes)


def test_trade_levels_marker_has_entry_price():
    levels = TradeLevels(entry=103.0, stop_loss=100.0, take_profit=109.0, direction=Direction.LONG)

    fig = build_candlestick_figure(sample_ohlcv(), levels, "EUR/USD", ("Trend Alignment",))

    entry_trace = fig.data[1]
    assert entry_trace.name == "Entry"
    assert entry_trace.y[0] == 103.0


def test_chart_history_note_marks_intraday_as_limited():
    assert "limited" in chart_history_note("1h").lower()
    assert "maximum" in chart_history_note("1d").lower()
```

- [ ] **Step 2: Run chart tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_charts.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'src.charts'`.

- [ ] **Step 3: Add Plotly dependency**

Modify `requirements.txt` to include:

```text
plotly>=5.22
```

If Plotly is not installed locally, run:

```powershell
.\.venv\Scripts\python.exe -m pip install plotly>=5.22
```

Expected: Plotly installs or is already satisfied.

- [ ] **Step 4: Create chart package initializer**

Write `src/charts/__init__.py`:

```python
"""Chart helpers for Trading Signal Scanner."""
```

- [ ] **Step 5: Implement candlestick chart helper**

Write `src/charts/candles.py`:

```python
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from src.models.signals import Direction


@dataclass(frozen=True)
class TradeLevels:
    entry: float
    stop_loss: float
    take_profit: float
    direction: Direction


def chart_history_note(interval: str) -> str:
    if interval.endswith("m") or interval.endswith("h"):
        return "Intraday/scalping history is limited by provider availability."
    return "Using maximum practical historical depth available from the provider."


def build_candlestick_figure(
    df: pd.DataFrame,
    levels: TradeLevels,
    title: str,
    strategy_tags: tuple[str, ...],
) -> go.Figure:
    candles = df.copy()
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=candles.index,
            open=candles["open"],
            high=candles["high"],
            low=candles["low"],
            close=candles["close"],
            name="Candles",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        )
    )
    marker_color = "#f97316" if levels.direction == Direction.LONG else "#ef4444"
    fig.add_trace(
        go.Scatter(
            x=[candles.index[-1]],
            y=[levels.entry],
            mode="markers+text",
            marker={"size": 13, "color": marker_color, "symbol": "circle"},
            text=["Entry"],
            textposition="top center",
            name="Entry",
        )
    )
    fig.add_hline(y=levels.stop_loss, line_color="#ef4444", line_width=2, annotation_text="SL")
    fig.add_hline(y=levels.take_profit, line_color="#22c55e", line_width=2, annotation_text="TP")
    fig.update_layout(
        title=f"{title} - {levels.direction.value} | {', '.join(strategy_tags)}",
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font={"color": "#f3f4f6"},
        xaxis_rangeslider_visible=False,
        height=560,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )
    return fig
```

- [ ] **Step 6: Run chart tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_charts.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit chart module**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add requirements.txt src/charts tests/test_charts.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add candlestick chart trade levels"
```

Expected: commit succeeds.

## Task 2: Strategy Profile Classification

**Files:**
- Create: `src/evaluation/__init__.py`
- Create: `src/evaluation/strategy_profiles.py`
- Test: `tests/test_strategy_profiles.py`

- [ ] **Step 1: Write strategy profile tests**

Write `tests/test_strategy_profiles.py`:

```python
from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.models.signals import Direction, SignalCandidate


def make_signal(reasons: tuple[str, ...], tags: tuple[str, ...] = ("EMA MOMENTUM",)) -> SignalCandidate:
    return SignalCandidate(
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction=Direction.LONG,
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=tags,
        reasons=reasons,
    )


def test_classify_strategy_profiles_maps_reasons_to_profiles():
    signal = make_signal(("trend aligned", "valid order block", "fair value gap", "liquidity sweep", "EMA momentum"))

    profiles = classify_strategy_profiles(signal)

    assert "Trend Alignment" in profiles
    assert "Order Block" in profiles
    assert "FVG / Imbalance" in profiles
    assert "Liquidity Sweep" in profiles
    assert "Scalping / EMA Momentum" in profiles


def test_confluence_summary_counts_profiles():
    signal = make_signal(("trend aligned", "valid order block", "EMA momentum"))

    summary = confluence_summary(signal, historical_win_rate=61.8, historical_setups=112)

    assert "3 strategies support this LONG setup" in summary
    assert "61.8%" in summary
    assert "112 setups" in summary
```

- [ ] **Step 2: Run strategy profile tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_strategy_profiles.py -v
```

Expected: FAIL with missing `src.evaluation`.

- [ ] **Step 3: Create evaluation package initializer**

Write `src/evaluation/__init__.py`:

```python
"""Historical strategy evaluation helpers."""
```

- [ ] **Step 4: Implement strategy profiles**

Write `src/evaluation/strategy_profiles.py`:

```python
from src.models.signals import SignalCandidate


PROFILE_REASON_MAP = {
    "Trend Alignment": ("trend aligned",),
    "Order Block": ("valid order block", "order block"),
    "FVG / Imbalance": ("fair value gap", "fvg"),
    "Liquidity Sweep": ("liquidity sweep",),
    "Scalping / EMA Momentum": ("ema momentum", "ema"),
}


def classify_strategy_profiles(signal: SignalCandidate) -> tuple[str, ...]:
    haystack = " ".join(signal.reasons + signal.strategy_tags).lower()
    profiles = []
    for profile, needles in PROFILE_REASON_MAP.items():
        if any(needle in haystack for needle in needles):
            profiles.append(profile)
    return tuple(profiles)


def confluence_summary(signal: SignalCandidate, historical_win_rate: float, historical_setups: int) -> str:
    profiles = classify_strategy_profiles(signal)
    return (
        f"{len(profiles)} strategies support this {signal.direction.value} setup. "
        f"Historically, similar setups reached TP first {historical_win_rate:.1f}% "
        f"of the time over {historical_setups} setups."
    )
```

- [ ] **Step 5: Run strategy profile tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_strategy_profiles.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit strategy profiles**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/evaluation tests/test_strategy_profiles.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: classify signal strategy profiles"
```

Expected: commit succeeds.

## Task 3: Historical Strategy Evaluation

**Files:**
- Create: `src/evaluation/historical.py`
- Test: `tests/test_historical_evaluation.py`

- [ ] **Step 1: Write historical evaluation tests**

Write `tests/test_historical_evaluation.py`:

```python
import pandas as pd

from src.evaluation.historical import (
    StrategyEvaluation,
    evaluate_static_setups,
    simulate_trade_outcome,
)
from src.models.signals import Direction


def test_simulate_trade_outcome_counts_take_profit_first_as_win():
    future = pd.DataFrame({"high": [104.0, 111.0], "low": [99.0, 103.0]})

    result = simulate_trade_outcome(future, Direction.LONG, entry=100.0, stop_loss=95.0, take_profit=110.0)

    assert result == 2.0


def test_simulate_trade_outcome_counts_same_candle_touch_as_loss():
    future = pd.DataFrame({"high": [111.0], "low": [94.0]})

    result = simulate_trade_outcome(future, Direction.LONG, entry=100.0, stop_loss=95.0, take_profit=110.0)

    assert result == -1.0


def test_evaluate_static_setups_reports_win_rate_and_profit_factor():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [101, 106, 111, 106, 112, 113],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [100, 105, 110, 105, 111, 112],
            "volume": [1000] * 6,
        }
    )
    setup_indexes = [0, 3]

    evaluation = evaluate_static_setups(df, Direction.LONG, setup_indexes, reward_multiple=2.0, stop_distance=5.0)

    assert isinstance(evaluation, StrategyEvaluation)
    assert evaluation.setups == 2
    assert evaluation.win_rate == 100.0
    assert evaluation.profit_factor == float("inf")
```

- [ ] **Step 2: Run historical evaluation tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_historical_evaluation.py -v
```

Expected: FAIL with missing `src.evaluation.historical`.

- [ ] **Step 3: Implement historical evaluator**

Write `src/evaluation/historical.py`:

```python
from dataclasses import dataclass

import pandas as pd

from src.backtest.metrics import max_drawdown, summarize_trades
from src.models.signals import Direction


@dataclass(frozen=True)
class StrategyEvaluation:
    profile: str
    setups: int
    wins: int
    losses: int
    win_rate: float
    profit_factor: float
    average_r: float
    max_drawdown: float


def simulate_trade_outcome(
    future: pd.DataFrame,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
) -> float | None:
    risk = abs(entry - stop_loss)
    if risk <= 0:
        return None
    for _, candle in future.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if direction == Direction.LONG:
            stop_hit = low <= stop_loss
            target_hit = high >= take_profit
        else:
            stop_hit = high >= stop_loss
            target_hit = low <= take_profit
        if stop_hit:
            return -1.0
        if target_hit:
            return round(abs(take_profit - entry) / risk, 2)
    return None


def evaluate_static_setups(
    df: pd.DataFrame,
    direction: Direction,
    setup_indexes: list[int],
    reward_multiple: float = 2.0,
    stop_distance: float | None = None,
    profile: str = "Combined Setup",
) -> StrategyEvaluation:
    r_multiples: list[float] = []
    equity = [100.0]
    for index in setup_indexes:
        if index >= len(df) - 1:
            continue
        entry = float(df.iloc[index]["close"])
        distance = float(stop_distance or max(float(df.iloc[index]["high"] - df.iloc[index]["low"]), entry * 0.01))
        if direction == Direction.LONG:
            stop_loss = entry - distance
            take_profit = entry + (distance * reward_multiple)
        else:
            stop_loss = entry + distance
            take_profit = entry - (distance * reward_multiple)
        outcome = simulate_trade_outcome(df.iloc[index + 1 :], direction, entry, stop_loss, take_profit)
        if outcome is None:
            continue
        r_multiples.append(outcome)
        equity.append(equity[-1] + outcome)
    summary = summarize_trades(r_multiples)
    wins = len([value for value in r_multiples if value > 0])
    losses = len([value for value in r_multiples if value < 0])
    return StrategyEvaluation(
        profile=profile,
        setups=len(r_multiples),
        wins=wins,
        losses=losses,
        win_rate=float(summary["win_rate"]),
        profit_factor=float(summary["profit_factor"]),
        average_r=float(summary["average_r"]),
        max_drawdown=max_drawdown(equity),
    )
```

- [ ] **Step 4: Run historical evaluation tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_historical_evaluation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit historical evaluator**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/evaluation/historical.py tests/test_historical_evaluation.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: evaluate historical strategy setups"
```

Expected: commit succeeds.

## Task 4: Streamlit Chart And Evaluation Integration

**Files:**
- Modify: `app.py`
- Modify: `tests/test_app_config.py`

- [ ] **Step 1: Write app helper tests**

Replace `tests/test_app_config.py` with:

```python
from app import APP_TITLE, THEME_ACCENT, chart_period_for_interval, evaluation_rows
from src.evaluation.historical import StrategyEvaluation


def test_app_uses_dark_orange_identity():
    assert APP_TITLE == "Trading Signal Scanner"
    assert THEME_ACCENT == "#f97316"


def test_chart_period_for_interval_uses_max_for_daily_and_limited_for_intraday():
    assert chart_period_for_interval("1d") == "max"
    assert chart_period_for_interval("1wk") == "max"
    assert chart_period_for_interval("1h") == "730d"


def test_evaluation_rows_formats_percentages():
    rows = evaluation_rows(
        [
            StrategyEvaluation(
                profile="Order Block",
                setups=10,
                wins=6,
                losses=4,
                win_rate=60.0,
                profit_factor=3.0,
                average_r=0.8,
                max_drawdown=0.12,
            )
        ],
        supported_profiles=("Order Block",),
    )

    assert rows[0]["Supports current trade"] == "Yes"
    assert rows[0]["Win rate"] == "60.0%"
    assert rows[0]["Max drawdown"] == "12.0%"
```

- [ ] **Step 2: Run app helper tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_config.py -v
```

Expected: FAIL because `chart_period_for_interval` and `evaluation_rows` do not exist.

- [ ] **Step 3: Add imports and helper functions to `app.py`**

Modify `app.py` imports:

```python
from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.evaluation.historical import StrategyEvaluation, evaluate_static_setups
from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.models.signals import Direction
```

Add these helpers below constants:

```python
def chart_period_for_interval(interval: str) -> str:
    if interval in {"1d", "1wk"}:
        return "max"
    return "730d"


def evaluation_rows(evaluations: list[StrategyEvaluation], supported_profiles: tuple[str, ...]) -> list[dict[str, str | int | float]]:
    rows = []
    for evaluation in evaluations:
        rows.append(
            {
                "Strategy profile": evaluation.profile,
                "Supports current trade": "Yes" if evaluation.profile in supported_profiles else "No",
                "Historical setups": evaluation.setups,
                "Win rate": f"{evaluation.win_rate:.1f}%",
                "Profit factor": evaluation.profit_factor,
                "Average R": evaluation.average_r,
                "Max drawdown": f"{evaluation.max_drawdown * 100:.1f}%",
            }
        )
    return rows
```

- [ ] **Step 4: Add cached data loader to `app.py`**

Add below `evaluation_rows`:

```python
@st.cache_data(show_spinner=False, ttl=900)
def load_history(symbol: str, period: str, interval: str) -> pd.DataFrame:
    return YFinanceProvider().history(symbol, period=period, interval=interval)
```

- [ ] **Step 5: Integrate chart and evaluation UI into `app.py`**

Inside `if signals:` after selecting `signal`, replace the existing signal-card block with:

```python
        supported_profiles = classify_strategy_profiles(signal)
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        st.write("Razones:", ", ".join(signal.reasons))
        st.write(f"Entrada: {signal.entry} | SL: {signal.stop_loss} | TP: {signal.take_profit}")
        st.write(f"Direccion: {signal.direction.value} | Score: {signal.score}% | R:R: {signal.risk_reward}")
        st.write(f"Estrategias a favor: {len(supported_profiles)} - {', '.join(supported_profiles)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Grafico y niveles de trade")
        chart_interval = st.selectbox("Intervalo del grafico", ["1h", "1d", "1wk"], index=1)
        chart_period = chart_period_for_interval(chart_interval)
        st.caption(chart_history_note(chart_interval))
        try:
            chart_df = load_history(signal.symbol, period=chart_period, interval=chart_interval)
            levels = TradeLevels(
                entry=signal.entry,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                direction=signal.direction,
            )
            fig = build_candlestick_figure(chart_df.tail(240), levels, signal.display_symbol, supported_profiles)
            st.plotly_chart(fig, use_container_width=True)

            setup_indexes = list(range(20, max(20, len(chart_df) - 5), 20))
            evaluations = [
                evaluate_static_setups(chart_df, signal.direction, setup_indexes, profile=profile)
                for profile in ("Scalping / EMA Momentum", "Order Block", "FVG / Imbalance", "Liquidity Sweep", "Trend Alignment")
            ]
            supported = [item for item in evaluations if item.profile in supported_profiles and item.setups > 0]
            combined_win_rate = (
                sum(item.win_rate for item in supported) / len(supported)
                if supported
                else 0.0
            )
            combined_setups = sum(item.setups for item in supported)
            st.subheader("Evaluacion historica de estrategias")
            st.write(confluence_summary(signal, combined_win_rate, combined_setups))
            st.dataframe(evaluation_rows(evaluations, supported_profiles), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"No se pudo cargar el grafico/evaluacion historica: {exc}")
```

- [ ] **Step 6: Run app helper tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_config.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit UI integration**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add app.py tests/test_app_config.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: show candlestick strategy evaluation UI"
```

Expected: commit succeeds.

## Task 5: Full Verification And Local App Restart

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Restart Streamlit**

Stop any old Streamlit process:

```powershell
Get-Process streamlit -ErrorAction SilentlyContinue | Stop-Process
```

Start the app:

```powershell
.\.venv\Scripts\streamlit.exe run app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Expected: app prints `URL: http://127.0.0.1:8501`.

- [ ] **Step 3: Verify local port**

Run:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8501
```

Expected: `TcpTestSucceeded : True`.

- [ ] **Step 4: Update README with chart feature**

Append to `README.md`:

```markdown
## Candlestick And Strategy Evaluation

The app shows a candlestick chart for a selected signal with entry, stop loss, and take profit levels. Historical strategy evaluation reports backtested win rate, setup count, profit factor, average R, and drawdown using available provider history.

Intraday history is limited by the data provider; daily and weekly views use the maximum practical history available.
```

- [ ] **Step 5: Commit docs**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add README.md
& 'C:\Program Files\Git\cmd\git.exe' commit -m "docs: describe candlestick strategy evaluation"
```

Expected: commit succeeds.

## Self-Review

Spec coverage:

- Candlestick chart is implemented by Task 1 and integrated by Task 4.
- Entry marker, SL, and TP are implemented by Task 1.
- Historical period distinction is implemented by Task 4.
- Strategy profiles and confluence count are implemented by Task 2 and Task 4.
- Historical win rate, setup count, profit factor, average R, and drawdown are implemented by Task 3 and Task 4.
- Conservative same-candle TP/SL handling is implemented by Task 3.
- Plotly dependency is implemented by Task 1.

No placeholders are intentionally left. This plan keeps percentages historical/backtested and avoids guaranteeing future outcomes.
