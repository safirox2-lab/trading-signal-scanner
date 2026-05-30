from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd

from src.backtest.metrics import max_drawdown, summarize_trades
from src.indicators.imbalance import fair_value_gaps
from src.indicators.trend import ema
from src.indicators.volatility import atr
from src.models.signals import Direction
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


@dataclass(frozen=True)
class ProfileTradeLevels:
    profile: str
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    setup_index: int


def _trade_outcome_from_arrays(
    high_values: Sequence[float],
    low_values: Sequence[float],
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
) -> float | None:
    risk = abs(entry - stop_loss)
    if risk <= 0:
        return None
    for high_value, low_value in zip(high_values, low_values):
        high = float(high_value)
        low = float(low_value)
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


def simulate_trade_outcome(
    future: pd.DataFrame,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
) -> float | None:
    return _trade_outcome_from_arrays(
        future["high"].to_numpy(),
        future["low"].to_numpy(),
        direction,
        entry,
        stop_loss,
        take_profit,
    )


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
    close_values = df["close"].astype(float).to_numpy()
    high_values = df["high"].astype(float).to_numpy()
    low_values = df["low"].astype(float).to_numpy()
    atr_values = atr(df, period=14).astype(float).to_numpy()
    evaluations: list[StrategyEvaluation] = []
    for config in strategy_profile_configs(df, direction):
        r_multiples: list[float] = []
        equity = [100.0]
        for index in config.setup_indexes:
            if index >= len(df) - 1:
                continue
            entry = float(close_values[index])
            atr_value = float(atr_values[index])
            candle_range = float(high_values[index] - low_values[index])
            distance = max(atr_value * config.atr_stop_multiple, candle_range, entry * 0.001)
            if direction == Direction.LONG:
                stop_loss = entry - distance
                take_profit = entry + (distance * config.reward_multiple)
            else:
                stop_loss = entry + distance
                take_profit = entry - (distance * config.reward_multiple)
            outcome = _trade_outcome_from_arrays(
                high_values[index + 1 :],
                low_values[index + 1 :],
                direction,
                entry,
                stop_loss,
                take_profit,
            )
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


def latest_trade_levels_for_profile(
    df: pd.DataFrame,
    direction: Direction,
    profile: str,
) -> ProfileTradeLevels | None:
    configs = {config.profile: config for config in strategy_profile_configs(df, direction)}
    config = configs.get(profile)
    if config is None or not config.setup_indexes:
        return None
    eligible_indexes = [index for index in config.setup_indexes if index < len(df)]
    if not eligible_indexes:
        return None
    setup_index = max(eligible_indexes)
    latest_atr = atr(df, period=14)
    entry = float(df.iloc[setup_index]["close"])
    atr_value = float(latest_atr.iloc[setup_index])
    candle_range = float(df.iloc[setup_index]["high"] - df.iloc[setup_index]["low"])
    distance = max(atr_value * config.atr_stop_multiple, candle_range, entry * 0.001)
    if direction == Direction.LONG:
        stop_loss = entry - distance
        take_profit = entry + (distance * config.reward_multiple)
    else:
        stop_loss = entry + distance
        take_profit = entry - (distance * config.reward_multiple)
    return ProfileTradeLevels(
        profile=profile,
        entry=round(entry, 5),
        stop_loss=round(stop_loss, 5),
        take_profit=round(take_profit, 5),
        risk_reward=config.reward_multiple,
        setup_index=setup_index,
    )


def _ema_momentum_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    fast = ema(df["close"], 9)
    slow = ema(df["close"], 21)
    if direction == Direction.LONG:
        crosses = fast.shift(1).le(slow.shift(1)) & fast.gt(slow)
    else:
        crosses = fast.shift(1).ge(slow.shift(1)) & fast.lt(slow)
    return [index for index, crossed in enumerate(crosses.to_numpy()) if crossed and 0 < index < len(df) - 1]


def _order_block_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "long" if direction == Direction.LONG else "short"
    return [int(block["index"]) for block in order_block_candidates(df, impulse_multiplier=1.2) if block["direction"] == wanted]


def _fvg_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "bullish" if direction == Direction.LONG else "bearish"
    gaps = fair_value_gaps(df)
    if "type" not in gaps:
        return []
    matches = gaps["type"].eq(wanted).to_numpy()
    return [index for index, matched in enumerate(matches) if matched and index < len(df) - 1]


def _liquidity_sweep_indexes(df: pd.DataFrame, direction: Direction) -> list[int]:
    wanted = "bullish_sweep" if direction == Direction.LONG else "bearish_sweep"
    high_values = df["high"].astype(float).to_numpy()
    low_values = df["low"].astype(float).to_numpy()
    close_values = df["close"].astype(float).to_numpy()
    indexes = []
    for index in range(2, len(df) - 1):
        equal_high = abs(high_values[index - 2] - high_values[index - 1]) <= 0.05
        equal_low = abs(low_values[index - 2] - low_values[index - 1]) <= 0.05
        prior_high = max(high_values[index - 2], high_values[index - 1])
        prior_low = min(low_values[index - 2], low_values[index - 1])
        bearish_sweep = equal_high and high_values[index] > prior_high and close_values[index] < prior_high
        bullish_sweep = equal_low and low_values[index] < prior_low and close_values[index] > prior_low
        sweep = None
        if bearish_sweep:
            sweep = "bearish_sweep"
        elif bullish_sweep:
            sweep = "bullish_sweep"
        if sweep == wanted:
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
