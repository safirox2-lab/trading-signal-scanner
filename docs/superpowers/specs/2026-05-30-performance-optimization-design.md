# Performance Optimization Design

## Goal

Improve perceived and measured performance of the Streamlit trading scanner without changing trading semantics or the main user workflow. The first target is historical strategy evaluation, which measured at about 12.3 seconds for 5,000 synthetic candles during exploration. The second target is Streamlit compatibility and small UI/runtime friction found in logs.

## Scope

- Optimize `src/evaluation/historical.py` where repeated Pandas slicing and row iteration make historical evaluation slow.
- Keep outcome behavior unchanged: if stop loss and take profit are touched in the same candle, the stop loss wins.
- Keep scanner inputs, journal lifecycle, chart snapshot behavior, and visible tab structure unchanged.
- Replace deprecated Streamlit `use_container_width=True` calls with `width="stretch"`.
- Add focused tests or assertions that protect the optimized evaluation behavior and UI helper compatibility.
- Capture a lightweight before/after timing on synthetic data as verification evidence.

## Non-Goals

- No strategy rule changes.
- No redesign of the Command Center interface.
- No database schema changes.
- No change to yfinance provider behavior.
- No aggressive snapshot storage rewrite in this pass.

## Architecture

The main performance work stays inside `src/evaluation/historical.py`. The current implementation asks each profile for setup indexes, then simulates each setup by iterating future candles. That is correct but expensive when history is large. The optimized version should reduce repeated Series slicing and DataFrame row access by using precomputed arrays where practical.

The EMA momentum profile should detect crosses from full fast/slow EMA Series once, instead of repeatedly slicing partial Series and calling `ema_cross_direction` for each index. Liquidity sweep detection can also avoid constructing many small DataFrame slices if a simple rolling-window calculation preserves the same semantics.

Trade outcome simulation may continue to scan future candles setup-by-setup, but it should use column arrays rather than `iterrows()` to reduce Pandas overhead. The implementation must remain readable and small enough to audit because this is financial-analysis logic.

## Data Flow

1. `app.py` loads chart history through cached `load_history`.
2. `cached_strategy_evaluations` calls `evaluate_strategy_profiles`.
3. `evaluate_strategy_profiles` computes profile setup indexes and simulates outcomes.
4. Results flow back to `evaluation_rows` and Streamlit tables.

The optimization does not change this flow. It only reduces overhead inside step 3 and modernizes Streamlit rendering calls.

## Error Handling

Existing behavior remains: empty or invalid data raises through provider/model validation and the UI catches chart/evaluation exceptions with a warning. Optimized code should keep defensive checks for zero or invalid risk distance and avoid introducing broad exception swallowing.

## Testing

- Run the full suite with `.\.venv\Scripts\python.exe -m pytest -q`.
- Add or update tests if implementation changes public helper behavior.
- Run a synthetic timing command for `evaluate_strategy_profiles` before and after implementation to confirm the bottleneck improves.
- Run `.\.venv\Scripts\python.exe -m compileall app.py src`.

## Follow-Up Suggestions

- Add a bounded history option for evaluation if users regularly select daily or weekly maximum history.
- Store chart snapshot metadata plus compact data instead of full Plotly figure JSON if the journal grows large.
- Add optional timing logs around scan, history loading, evaluation, and chart rendering for future profiling.

## Self-Review

No placeholders remain. The scope is focused on performance and compatibility, not strategy changes. The design keeps existing data flow and explicitly preserves same-candle SL-first semantics. Verification requirements are concrete and tied to commands already used by the project.
