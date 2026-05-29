from dataclasses import dataclass

import pandas as pd

from src.backtest.metrics import max_drawdown, summarize_trades
from src.indicators.imbalance import fair_value_gaps
from src.indicators.momentum import ema_cross_direction
from src.indicators.trend import ema
from src.indicators.volatility import atr
from src.models.signals import Direction
from src.strategies.liquidity import liquidity_sweep
from src.strategies.order_blocks import order_block_candidates


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


@dataclass(frozen=True)
class StrategyProfileConfig:
    profile: str
    reward_multiple: float
    atr_stop_multiple: float
    setup_indexes: list[int]


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


def strategy_profile_configs(df: pd.DataFrame, direction: Direction) -> list[StrategyProfileConfig]:
    return [
        StrategyProfileConfig("Scalping / EMA Momentum", 1.2, 0.8, _ema_momentum_indexes(df, direction)),
        StrategyProfileConfig("Order Block", 2.5, 1.4, _order_block_indexes(df, direction)),
        StrategyProfileConfig("FVG / Imbalance", 2.0, 1.0, _fvg_indexes(df, direction)),
        StrategyProfileConfig("Liquidity Sweep", 2.2, 1.2, _liquidity_sweep_indexes(df, direction)),
        StrategyProfileConfig("Trend Alignment", 1.8, 1.1, _trend_alignment_indexes(df, direction)),
    ]


def evaluate_strategy_profiles(df: pd.DataFrame, direction: Direction) -> list[StrategyEvaluation]:
    latest_atr = atr(df, period=14)
    evaluations: list[StrategyEvaluation] = []
    for config in strategy_profile_configs(df, direction):
        r_multiples: list[float] = []
        equity = [100.0]
        for index in config.setup_indexes:
            if index >= len(df) - 1:
                continue
            entry = float(df.iloc[index]["close"])
            atr_value = float(latest_atr.iloc[index])
            candle_range = float(df.iloc[index]["high"] - df.iloc[index]["low"])
            distance = max(atr_value * config.atr_stop_multiple, candle_range, entry * 0.001)
            if direction == Direction.LONG:
                stop_loss = entry - distance
                take_profit = entry + (distance * config.reward_multiple)
            else:
                stop_loss = entry + distance
                take_profit = entry - (distance * config.reward_multiple)
            outcome = simulate_trade_outcome(df.iloc[index + 1 :], direction, entry, stop_loss, take_profit)
            if outcome is None:
                continue
            r_multiples.append(outcome)
            equity.append(equity[-1] + outcome)

        summary = summarize_trades(r_multiples)
        wins = len([value for value in r_multiples if value > 0])
        losses = len([value for value in r_multiples if value < 0])
        evaluations.append(
            StrategyEvaluation(
                profile=config.profile,
                setups=len(r_multiples),
                wins=wins,
                losses=losses,
                win_rate=float(summary["win_rate"]),
                profit_factor=float(summary["profit_factor"]),
                average_r=float(summary["average_r"]),
                max_drawdown=max_drawdown(equity),
            )
        )
    return evaluations


def _ema_momentum_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    fast = ema(df["close"], 9)
    slow = ema(df["close"], 21)
    indexes = []
    for index in range(1, len(df) - 1):
        cross = ema_cross_direction(fast.iloc[: index + 1], slow.iloc[: index + 1])
        if direction == Direction.LONG and cross == "long":
            indexes.append(index)
        if direction == Direction.SHORT and cross == "short":
            indexes.append(index)
    return indexes


def _order_block_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "long" if direction == Direction.LONG else "short"
    return [int(block["index"]) for block in order_block_candidates(df, impulse_multiplier=1.2) if block["direction"] == wanted]


def _fvg_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "bullish" if direction == Direction.LONG else "bearish"
    gaps = fair_value_gaps(df)
    return [index for index, row in enumerate(gaps.to_dict("records")) if row["type"] == wanted and index < len(df) - 1]


def _liquidity_sweep_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "bullish_sweep" if direction == Direction.LONG else "bearish_sweep"
    indexes = []
    for index in range(2, len(df) - 1):
        if liquidity_sweep(df.iloc[index - 2 : index + 1], tolerance=0.05) == wanted:
            indexes.append(index)
    return indexes


def _trend_alignment_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    close = df["close"].astype(float)
    fast = ema(close, 20)
    slow = ema(close, 50)
    indexes = []
    for index in range(50, len(df) - 1):
        if direction == Direction.LONG and close.iloc[index] > slow.iloc[index] and fast.iloc[index] > slow.iloc[index]:
            indexes.append(index)
        if direction == Direction.SHORT and close.iloc[index] < slow.iloc[index] and fast.iloc[index] < slow.iloc[index]:
            indexes.append(index)
    return indexes
