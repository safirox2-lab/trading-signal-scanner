# Same Strategy Chart Snapshots Design

## Goal

Fix chart comparison so `Antes` and `Despues` compare only the same strategy on the same symbol, interval, and direction. When that same strategy produces a materially different entry, the app records a new recommendation and stores the before/after chart pair for later review.

## Behavior

- A chart snapshot is keyed by `symbol`, `interval`, `direction`, and `strategy`.
- `Antes/Despues` is shown only when the previous snapshot has the same key as the current chart.
- Switching from one strategy to another clears the comparison instead of comparing unrelated hypotheses.
- If the current same-strategy entry differs from the previous entry beyond a small tolerance, the app records:
  - a new `RecommendationRecord` for the updated entry;
  - a `chart_snapshots` row with before/after levels and Plotly figure JSON.
- Chart snapshot records are stored in SQLite and linked to the recommendation key.
- The history can list saved chart evolutions for review.

## Storage

Add a `chart_snapshots` SQLite table:

- `snapshot_key`
- `signal_key`
- `created_at`
- `symbol`
- `display_symbol`
- `direction`
- `timeframe`
- `strategy`
- before/after `entry`, `stop_loss`, `take_profit`
- before/after generated timestamp
- before/after Plotly JSON

## UI

- In the chart section, `Antes` appears only for the same strategy.
- If the selected strategy changes, only `Despues` appears for the newly selected strategy.
- In `Registro`, add a `Evolucion grafica guardada` table showing stored before/after entries.

## Out Of Scope

- Image export files.
- External object storage.
- Strategy self-modification.
