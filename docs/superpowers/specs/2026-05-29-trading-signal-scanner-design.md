# Trading Signal Scanner - Design

Date: 2026-05-29

## Purpose

Build a local trading analysis application that scans selected forex pairs, indices, and gold for long and short opportunities. The application will combine transparent technical indicators, institutional-style concepts from `Trading.txt`, risk management, and historical validation.

The application is an analysis and education tool. It does not guarantee profit, does not provide financial advice, and will not execute trades automatically in the first version.

## Approved Direction

Use a layered, realistic architecture:

- Start with free or low-friction data for prototyping and backtesting.
- Keep the data layer replaceable so broker or paid market data APIs can be added later.
- Treat TradingView as a charting, visual reference, or alert-webhook companion, not as the direct market-data source for the local app.
- Show a confidence score based on technical confluence and historical behavior, not as a guaranteed probability of profit.

## Initial Markets

The first scanner universe will focus on liquid instruments:

- Forex majors: `EUR/USD`, `GBP/USD`, `USD/JPY`, `AUD/USD`, `USD/CAD`.
- US indices or proxies: S&P 500, Nasdaq 100, Dow Jones.
- Gold: XAU/USD or a practical proxy such as gold futures/ETF data depending on provider support.

Exotic forex pairs are out of scope for the first version because spreads, data quality, and signal cleanliness are usually worse.

## Data Sources

Version 1 will use a provider abstraction:

- Initial provider: `yfinance`, useful for prototyping, research, and historical testing.
- Future providers: OANDA, Interactive Brokers, Polygon, Twelve Data, Alpaca, or another broker/data vendor with API keys.
- Optional future integration: TradingView alerts via webhooks into the local app.

The app must label data limitations clearly. If a provider is delayed, incomplete, or not suitable for live execution, the UI must show that.

## Strategies

### Trend And Regime Filter

Use EMA 50 and EMA 200 to classify market regime:

- Bullish: price and EMA 50 above EMA 200.
- Bearish: price and EMA 50 below EMA 200.
- Sideways or uncertain: mixed conditions.

Signals aligned with the higher-timeframe regime receive a higher score. Countertrend signals need stronger confirmation.

### EMA Momentum

Use EMA 9 and EMA 21 for momentum confirmation:

- Long confirmation: EMA 9 crosses above EMA 21.
- Short confirmation: EMA 9 crosses below EMA 21.

This strategy is not used alone as a final signal. It is a confluence factor.

### Order Blocks

Detect possible order blocks using measurable rules:

- Bullish order block: last bearish candle before a strong bullish impulse.
- Bearish order block: last bullish candle before a strong bearish impulse.
- The impulse must break a recent swing high or swing low.
- Prefer zones that have not already been mitigated.
- Entry reference can use the 50 percent body threshold or the wick boundary, depending on configuration.

### Structure Breaks

Detect basic BOS and ChoCH events:

- BOS: price breaks a recent swing in the direction of the trend.
- ChoCH: price breaks the prior structure in the opposite direction, suggesting possible reversal.

Swing detection must be deterministic, using a configurable lookback window.

### Fair Value Gaps

Detect three-candle imbalances:

- Bullish FVG: candle 1 high is below candle 3 low.
- Bearish FVG: candle 1 low is above candle 3 high.

FVGs can increase signal score or become take-profit targets.

### Liquidity Sweeps

Detect simple liquidity events:

- Equal highs or equal lows within a tolerance.
- Price briefly breaks above equal highs or below equal lows, then rejects.
- Sweeps near order block zones increase score.

### RSI And ATR Filters

Use RSI as an exhaustion filter:

- Avoid low-quality long entries when RSI is extremely overbought.
- Avoid low-quality short entries when RSI is extremely oversold.

Use ATR for volatility and stop placement:

- Stop loss can be based on ATR multiple or order block extreme.
- Avoid signals when ATR is too low for movement or too high for controlled risk.

## Scoring Model

Every candidate signal receives a score from 0 to 100.

Suggested initial weights:

- Higher-timeframe trend alignment: 20 points.
- Valid order block: 20 points.
- BOS or ChoCH confirmation: 15 points.
- FVG confluence or target: 10 points.
- Liquidity sweep: 10 points.
- EMA momentum confirmation: 10 points.
- Risk/reward at least 1:2: 10 points.
- ATR and RSI quality filter: 5 points.

The UI must call this a "confidence score" or "opportunity score", not a guaranteed win probability.

When enough backtest data exists, the displayed score can include the historical win rate of similar setups as a separate field.

## Risk Management

The application will calculate risk for every signal:

- Default account risk: 1 percent per trade.
- Position size = amount at risk divided by stop distance.
- Stop loss:
  - Long: below order block low or ATR-based stop.
  - Short: above order block high or ATR-based stop.
- Take profit:
  - Minimum target: 2R.
  - Optional target: nearest liquidity level or FVG.

Signals that cannot produce at least 1:2 risk/reward should be hidden by default or marked as low quality.

## Backtesting

The backtest module must simulate trades in chronological order:

- Inputs: OHLCV data, strategy configuration, initial balance, risk percent.
- Outputs:
  - Initial balance.
  - Final balance.
  - Number of trades.
  - Win rate.
  - Maximum drawdown.
  - Profit factor.
  - Average R multiple.

The first version should avoid over-optimization. Parameters should be conservative and visible in the UI or config.

## User Interface

Use Streamlit for the first local version.

Approved visual direction:

- Dark professional interface.
- Orange accents for scores, active filters, warnings, and key indicators.
- Green only for long/upside signals.
- Red only for short/downside signals and risk alerts.
- High contrast text for fast reading.
- Data-dense layout without marketing sections.

Main views:

- Scanner view:
  - Opportunities table sorted by score.
  - Symbol, direction, score, entry, stop loss, take profit, risk/reward, timeframe, strategy tags.
  - Filters for market, timeframe, direction, minimum score, minimum risk/reward.
- Signal detail:
  - Explanation of why the signal exists.
  - Indicator values and confluences.
  - Risk calculation and suggested SL/TP.
- Backtest view:
  - Select symbol, timeframe, date range, strategy profile.
  - Show metrics and trade log.
- Settings:
  - Data provider selection.
  - Account balance and risk percent.
  - Symbols and timeframes.
  - Strategy thresholds.

## Project Structure

```text
app.py
requirements.txt
README.md
src/
  data/
    providers.py
    yfinance_provider.py
  indicators/
    trend.py
    momentum.py
    volatility.py
    structure.py
    imbalance.py
  strategies/
    order_blocks.py
    liquidity.py
    ema_momentum.py
    scanner.py
  risk/
    position_sizing.py
    trade_plan.py
  backtest/
    engine.py
    metrics.py
  models/
    market.py
    signals.py
tests/
  test_indicators.py
  test_risk.py
  test_scoring.py
  test_backtest.py
```

## Error Handling

The app must handle:

- Missing data or empty provider responses.
- Unsupported symbols.
- Provider rate limits or network errors.
- Insufficient candles for an indicator.
- Signals with invalid stop distance.
- Incomplete volume data.

Errors should appear as clear UI messages, not raw stack traces.

## Testing Plan

Unit tests:

- EMA, RSI, ATR calculations.
- Swing high/low detection.
- FVG detection.
- Order block candidate detection.
- Risk sizing and SL/TP.
- Score calculation.
- Backtest metrics.

Manual verification:

- Run the Streamlit app locally.
- Scan default symbols.
- Run one backtest.
- Confirm no signal is shown without SL, TP, and risk/reward.

## Out Of Scope For Version 1

- Automatic trade execution.
- Guaranteed real-time institutional-grade market data.
- Machine-learning predictions.
- Broker account management.
- Complex portfolio optimization.
- Scraping TradingView.

## References

- TradingView Charting Library Datafeed API: https://www.tradingview.com/charting-library-docs/latest/connecting_data/datafeed-api/
- TradingView webhooks support article: https://www.tradingview.com/support/solutions/43000529348/
- yfinance project: https://pypi.org/project/yfinance/
- Streamlit documentation: https://docs.streamlit.io/
