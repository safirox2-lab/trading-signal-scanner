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
