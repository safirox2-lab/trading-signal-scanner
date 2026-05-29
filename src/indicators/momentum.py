import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    if period <= 0:
        raise ValueError("RSI period must be positive")
    delta = series.astype(float).diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    avg_gain = gains.rolling(period, min_periods=period).mean()
    avg_loss = losses.rolling(period, min_periods=period).mean()
    relative_strength = avg_gain / avg_loss.replace(0, pd.NA)
    result = 100 - (100 / (1 + relative_strength))
    return result.fillna(50).clip(0, 100)


def ema_cross_direction(fast: pd.Series, slow: pd.Series) -> str | None:
    if len(fast) < 2 or len(slow) < 2:
        return None
    previous_fast, current_fast = fast.iloc[-2], fast.iloc[-1]
    previous_slow, current_slow = slow.iloc[-2], slow.iloc[-1]
    if previous_fast <= previous_slow and current_fast > current_slow:
        return "long"
    if previous_fast >= previous_slow and current_fast < current_slow:
        return "short"
    return None
