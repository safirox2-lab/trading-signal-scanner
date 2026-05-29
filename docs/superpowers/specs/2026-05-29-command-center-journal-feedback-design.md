# Command Center Journal And Feedback Design

## Goal

Upgrade the app into a cleaner Command Center experience and improve the autonomous journal so it records the full lifecycle of each recommendation: when the app recommended it, when price actually reached the entry, whether TP or SL was hit, and what feedback the result gives about the strategies involved.

The app remains an educational analysis tool. It will not guarantee profit, place trades, or claim certainty.

## User Experience

The interface will use a dark Command Center style with clear color roles:

- Orange: primary actions and selected controls.
- Green: TP, wins, favorable outcome, positive R.
- Red: SL, losses, risk, negative R.
- Cyan/blue: informational states and market status.
- Muted dark panels: tables, filters, chart containers, and historical summaries.

The main app will be organized into three practical tabs:

- `Buscar`: scanner, filters, top opportunities, selected signal details, candlestick chart, strategy selector, and historical strategy evaluation.
- `Registro`: autonomous recommendation history with recommendation time, entry trigger time, TP/SL state, result, and notes.
- `Feedback`: strategy learning dashboard with hit rate, average R, missed entries, SL concentration, and improvement suggestions.

The first screen should feel operational rather than like a landing page. Controls should be compact, readable, and placed around the workflows users repeat often.

## Recommendation Lifecycle

Recommendations will move through these states:

1. `WAITING_ENTRY`: the app generated a recommendation, but later market data has not touched the recommended entry price yet.
2. `OPEN`: the market touched the entry price after the recommendation time. The app records `entry_triggered_at`.
3. `TP`: after entry, the market touched take profit before stop loss.
4. `SL`: after entry, the market touched stop loss before take profit.
5. `UNRESOLVED`: reserved for records that cannot be evaluated due to missing or insufficient market data.

Existing `OPEN` records from the current database will be treated as already active recommendations during migration if no entry timestamp is present. New records will start as `WAITING_ENTRY`.

## Journal Data

The journal record will include:

- `signal_key`
- `created_at`: when the recommendation was generated.
- `entry_triggered_at`: when the recommended entry price was first reached after `created_at`.
- `symbol`
- `display_symbol`
- `direction`
- `timeframe`
- `entry`
- `stop_loss`
- `take_profit`
- `score`
- `risk_reward`
- `strategy_tags`
- `reasons`
- `status`
- `outcome_r`
- `resolved_at`
- `resolution_note`
- `feedback`

SQLite remains the local storage layer. The store will perform additive schema migration with `ALTER TABLE` for new columns so older local databases continue to work.

## Resolution Logic

Resolution will evaluate only candles after the recommendation time when the history index contains timestamps.

For each open-like record:

- If status is `WAITING_ENTRY`, scan forward until price reaches entry.
- Once entry is reached, set `entry_triggered_at` and status to `OPEN`.
- After entry, continue scanning for TP or SL.
- If TP and SL occur in the same candle, keep the conservative current behavior: SL is treated as first.
- If no entry occurs, the recommendation remains `WAITING_ENTRY`.
- If entry occurs but neither TP nor SL is reached, the recommendation remains `OPEN`.

This avoids counting ideas as failed before the market actually reached the proposed entry.

## Feedback Logic

Feedback is generated from deterministic rules, not from vague AI claims:

- TP result: mark the strategy set as favorable and mention which tags contributed.
- SL result: suggest reviewing confirmation, volatility, entry distance, or strategy confluence.
- WAITING_ENTRY for a long time: suggest the entry may be too far from current price or require a tighter trigger.
- Strategy groups with low hit rate: suggest reducing weight until more confirmation exists.
- Strategy groups with better average R and enough samples: suggest prioritizing them in review.

Feedback text is stored per closed record and summarized in the `Feedback` tab.

## Metrics

The `Registro` and `Feedback` views will show:

- Total recommendations.
- Waiting entry count.
- Open count.
- TP count.
- SL count.
- Hit rate using only resolved `TP` and `SL`.
- Entry activation rate: records with entry triggered divided by total recommendations.
- Average R for resolved records.
- Hit rate by strategy.
- Average R by strategy.
- Missed entry count by strategy.
- Hit rate by symbol.

## UI Details

`Buscar`:

- Sidebar keeps market filters, timeframe, minimum score, capital, auto-record toggle, auto-scan toggle, refresh, and search action.
- Main area starts with compact metrics.
- Opportunity table is followed by a signal detail panel and wide candlestick chart.
- Strategy selector keeps visible win-rate labels.

`Registro`:

- A lifecycle table shows Created, Entry Triggered, Symbol, Direction, Entry, SL, TP, Status, Outcome R, Strategies, Feedback.
- Status can be filtered by `ALL`, `WAITING_ENTRY`, `OPEN`, `TP`, `SL`, and `UNRESOLVED`.
- A button updates recommendations using current market history.

`Feedback`:

- Summary metrics appear at the top.
- Strategy performance table shows wins, losses, waiting entries, hit rate, activation rate, average R, and feedback.
- A compact insight section lists best-performing and weakest strategy groups based on available samples.

## Error Handling

- Missing market data should not break the page; it should add a warning in the existing error expander.
- Records with insufficient data should remain unchanged unless the resolver can clearly classify them.
- Database migration must be idempotent.
- Streamlit Cloud local SQLite persistence can reset; README should keep warning users that durable history requires an external database.

## Testing

Tests will cover:

- New journal statuses and default record creation.
- Entry trigger detection before TP/SL resolution.
- WAITING_ENTRY records do not count as losses.
- Same-candle TP/SL remains conservative and resolves as SL after entry.
- SQLite migration adds new columns and can read old records.
- Journal summary includes activation rate and waiting count.
- Feedback generation for TP, SL, and waiting-entry cases.
- UI helper formatting for new journal rows and feedback rows.

## Out Of Scope

- Real broker integration.
- Automatic live order execution.
- Self-modifying trading strategies.
- External database integration.
- User authentication.
