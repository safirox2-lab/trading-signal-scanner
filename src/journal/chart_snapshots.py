from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ChartSnapshotRecord:
    snapshot_key: str
    signal_key: str
    created_at: datetime
    symbol: str
    display_symbol: str
    direction: str
    timeframe: str
    strategy: str
    before_entry: float
    before_stop_loss: float
    before_take_profit: float
    after_entry: float
    after_stop_loss: float
    after_take_profit: float
    before_generated_at: str
    after_generated_at: str
    before_figure_json: str
    after_figure_json: str


def chart_snapshot_key(metadata: dict[str, str | float]) -> str:
    return "|".join(
        [
            str(metadata["symbol"]),
            str(metadata["interval"]),
            str(metadata["direction"]),
            str(metadata["strategy"]),
        ]
    )


def same_snapshot_context(before: dict[str, str | float] | None, after: dict[str, str | float]) -> bool:
    if not before:
        return False
    return chart_snapshot_key(before) == chart_snapshot_key(after)


def entry_changed(
    before: dict[str, str | float],
    after: dict[str, str | float],
    tolerance: float,
) -> bool:
    return abs(float(after["entry"]) - float(before["entry"])) > tolerance
