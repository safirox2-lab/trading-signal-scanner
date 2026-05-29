# Candlestick Charts And Strategy Evaluation - Design

Date: 2026-05-29

## Purpose

Extend the local Trading Signal Scanner with TradingView-style candlestick charts, visual trade levels, and historical strategy evaluation. The user should be able to inspect the market visually, see the suggested entry/stop/take-profit levels on the chart, and understand which strategies support the trade and how they performed historically.

This remains an educational analysis tool. The displayed success percentage is based on historical backtesting rules and is not a guarantee of future profit.

## Approved Direction

Implement the enhancement in three layers:

- Charting layer: interactive candlestick charts with entry, stop loss, and take profit markers.
- Evaluation layer: historical testing of strategy setups over available market history.
- UI layer: strategy explanations, confluence count, and historical success metrics.

## Charting Requirements

Use Plotly candlestick charts inside Streamlit.

The chart must show:

- OHLC candles for the selected symbol and timeframe.
- A visible entry marker at the signal entry price.
- A red stop-loss line.
- A green take-profit line.
- Direction label: `LONG` or `SHORT`.
- Strategy tags used by the current signal.

Marker behavior:

- Entry marker should be visually prominent and use the orange/red accent requested by the user.
- Stop loss should be red.
- Take profit should be green.
- The chart should keep the dark visual identity of the app.

## Historical Data Scope

The app must use the maximum realistic history available from the configured data provider:

- For daily and weekly analysis: use `period="max"` when available.
- For intraday/scalping analysis: use shorter provider-supported periods because free intraday data usually does not exist from the beginning of the asset's history.

The UI must explain this distinction clearly:

- "Historical depth depends on provider availability."
- "Intraday/scalping history is usually limited."

The app must not fabricate candles or imply that unavailable intraday history was tested.

## Strategy Profiles

The app will classify signal support into strategy profiles:

- `Scalping / EMA Momentum`: EMA 9/21 momentum with short timeframe context.
- `Order Block`: valid order block plus price context.
- `FVG / Imbalance`: fair value gap confluence or target.
- `Liquidity Sweep`: equal high/low sweep and rejection.
- `Trend Alignment`: higher-timeframe or current-period trend regime alignment.

Each signal detail panel must show:

- Strategies supporting the signal.
- Number of supporting strategies.
- Reasons produced by the scoring model.
- Whether the signal is mostly trend-following, reversal, or momentum-based.

## Historical Evaluation

Create a historical evaluator that tests strategy setups over past candles.

For each strategy profile and symbol, calculate:

- Number of historical setups.
- Number of wins where take profit was reached before stop loss.
- Number of losses where stop loss was reached before take profit.
- Win rate.
- Profit factor.
- Maximum drawdown.
- Average R multiple.

The evaluator should use deterministic rules:

- Entry: close price of the setup candle or the detected trade-plan entry.
- Stop loss: ATR-based or order-block extreme, matching current scanner behavior.
- Take profit: default 2R.
- Result: win if TP is reached before SL in future candles; loss if SL is reached first.

If both TP and SL are touched in the same candle, use a conservative assumption:

- For long trades, count the stop loss first.
- For short trades, count the stop loss first.

This avoids overstating win rate.

## Success Percentage

The app must show success percentage as historical win rate:

```text
Historical win rate: 63.4% over 112 setups
```

The UI must not label this as guaranteed probability. Use:

- `Historical win rate`
- `Backtested success`
- `Setup history`

Avoid:

- `Guaranteed success`
- `Profit probability`
- `Safe trade`

## User Interface Changes

Add a new section below the opportunities table:

### Chart And Trade Levels

Controls:

- Selected signal.
- Chart period.
- Chart interval.
- Toggle for showing historical strategy markers.

Display:

- Candlestick chart.
- Entry marker.
- SL and TP lines.
- Strategy tags on or near the chart.

### Strategy Evaluation

Display a compact table:

- Strategy profile.
- Supports current trade: yes/no.
- Historical setups.
- Win rate.
- Profit factor.
- Average R.
- Max drawdown.

Also show a short summary:

```text
4 strategies support this LONG setup. Historically, similar setups reached TP first 61.8% of the time on this symbol and timeframe.
```

## Data And Performance

Historical evaluation can be expensive. The first version should:

- Cache provider data with Streamlit caching.
- Limit historical marker rendering to avoid slow charts.
- Evaluate selected symbol in detail instead of all symbols at once.
- Keep scanner table fast by only running detailed history after a signal is selected.

## Testing Plan

Unit tests:

- Chart data conversion keeps OHLC columns.
- Trade marker structure contains entry, stop loss, and take profit.
- Historical evaluator counts wins and losses correctly.
- Conservative same-candle TP/SL behavior counts as loss.
- Strategy profile summary returns strategy names and win rate.

Manual verification:

- Open the local Streamlit app.
- Select a signal.
- Confirm candlestick chart renders.
- Confirm entry marker, SL line, and TP line are visible.
- Confirm strategy evaluation table appears.
- Confirm intraday historical limitation message appears when using intraday intervals.

## Out Of Scope

- Recreating the full TradingView product.
- Drawing manual user trendlines.
- Broker execution.
- Live order placement.
- Fabricating unavailable historical intraday data.
- Machine-learning optimization.

## Dependencies

Add Plotly to runtime dependencies:

```text
plotly>=5.22
```

## Files To Add Or Modify

- Modify: `requirements.txt`
- Modify: `app.py`
- Modify: `src/models/signals.py`
- Create: `src/charts/candles.py`
- Create: `src/evaluation/strategy_profiles.py`
- Create: `src/evaluation/historical.py`
- Create: `tests/test_charts.py`
- Create: `tests/test_historical_evaluation.py`
