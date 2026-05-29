import pandas as pd


def swing_points(df: pd.DataFrame, window: int = 2) -> pd.DataFrame:
    if window <= 0:
        raise ValueError("Swing window must be positive")
    highs = df["high"].astype(float)
    lows = df["low"].astype(float)
    result = pd.DataFrame(index=df.index)
    result["swing_high"] = False
    result["swing_low"] = False
    for index in range(window, len(df) - window):
        high_slice = highs.iloc[index - window : index + window + 1]
        low_slice = lows.iloc[index - window : index + window + 1]
        result.iloc[index, result.columns.get_loc("swing_high")] = highs.iloc[index] == high_slice.max()
        result.iloc[index, result.columns.get_loc("swing_low")] = lows.iloc[index] == low_slice.min()
    return result


def latest_structure_break(df: pd.DataFrame, window: int = 2) -> str | None:
    swings = swing_points(df, window=window)
    close = df["close"].astype(float)
    previous_swings = swings.iloc[:-1]
    prior_df = df.loc[previous_swings.index]
    swing_highs = prior_df.loc[previous_swings["swing_high"], "high"]
    swing_lows = prior_df.loc[previous_swings["swing_low"], "low"]
    if not swing_highs.empty and close.iloc[-1] > float(swing_highs.iloc[-1]):
        return "bullish_bos"
    if not swing_lows.empty and close.iloc[-1] < float(swing_lows.iloc[-1]):
        return "bearish_bos"
    return None
