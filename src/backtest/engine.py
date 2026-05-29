import pandas as pd

from src.backtest.metrics import max_drawdown, summarize_trades
from src.models.signals import Direction


def backtest_static_plan(
    df: pd.DataFrame,
    direction: Direction,
    entry: float,
    stop_loss: float,
    take_profit: float,
    initial_balance: float,
    risk_percent: float = 1.0,
) -> dict[str, float]:
    risk_amount = initial_balance * (risk_percent / 100)
    risk_distance = abs(entry - stop_loss)
    if risk_distance <= 0:
        raise ValueError("Risk distance must be positive")
    equity = [initial_balance]
    r_multiples: list[float] = []
    for _, candle in df.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if direction == Direction.LONG:
            if low <= stop_loss:
                r_multiples.append(-1.0)
                equity.append(equity[-1] - risk_amount)
                break
            if high >= take_profit:
                reward = abs(take_profit - entry) / risk_distance
                r_multiples.append(reward)
                equity.append(equity[-1] + (risk_amount * reward))
                break
        else:
            if high >= stop_loss:
                r_multiples.append(-1.0)
                equity.append(equity[-1] - risk_amount)
                break
            if low <= take_profit:
                reward = abs(entry - take_profit) / risk_distance
                r_multiples.append(reward)
                equity.append(equity[-1] + (risk_amount * reward))
                break
    summary = summarize_trades(r_multiples)
    summary["initial_balance"] = initial_balance
    summary["final_balance"] = round(equity[-1], 2)
    summary["max_drawdown"] = max_drawdown(equity)
    return summary
