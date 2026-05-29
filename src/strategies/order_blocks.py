import pandas as pd


def order_block_candidates(df: pd.DataFrame, impulse_multiplier: float = 1.5) -> list[dict[str, float | int | str]]:
    if len(df) < 3:
        return []
    ranges = (df["high"].astype(float) - df["low"].astype(float)).rolling(3, min_periods=1).mean()
    blocks: list[dict[str, float | int | str]] = []
    for index in range(1, len(df)):
        previous = df.iloc[index - 1]
        current = df.iloc[index]
        current_range = float(current["high"] - current["low"])
        average_range = float(ranges.iloc[index - 1])
        if average_range <= 0 or current_range < average_range * impulse_multiplier:
            continue
        previous_bearish = float(previous["close"]) < float(previous["open"])
        previous_bullish = float(previous["close"]) > float(previous["open"])
        current_bullish = float(current["close"]) > float(current["open"])
        current_bearish = float(current["close"]) < float(current["open"])
        if previous_bearish and current_bullish:
            blocks.append(
                {
                    "index": index - 1,
                    "direction": "long",
                    "low": float(previous["low"]),
                    "high": float(previous["high"]),
                    "mid": float((previous["open"] + previous["close"]) / 2),
                }
            )
        if previous_bullish and current_bearish:
            blocks.append(
                {
                    "index": index - 1,
                    "direction": "short",
                    "low": float(previous["low"]),
                    "high": float(previous["high"]),
                    "mid": float((previous["open"] + previous["close"]) / 2),
                }
            )
    return blocks
