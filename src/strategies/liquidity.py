import pandas as pd


def liquidity_sweep(df: pd.DataFrame, tolerance: float = 0.001) -> str | None:
    if len(df) < 3:
        return None
    prior = df.iloc[-3:-1]
    current = df.iloc[-1]
    equal_high = abs(float(prior["high"].iloc[0]) - float(prior["high"].iloc[1])) <= tolerance
    equal_low = abs(float(prior["low"].iloc[0]) - float(prior["low"].iloc[1])) <= tolerance
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    if equal_high and float(current["high"]) > prior_high and float(current["close"]) < prior_high:
        return "bearish_sweep"
    if equal_low and float(current["low"]) < prior_low and float(current["close"]) > prior_low:
        return "bullish_sweep"
    return None
