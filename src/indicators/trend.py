import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    if span <= 0:
        raise ValueError("EMA span must be positive")
    return series.astype(float).ewm(span=span, adjust=False).mean()


def trend_regime(df: pd.DataFrame, fast_span: int = 50, slow_span: int = 200) -> str:
    close = df["close"].astype(float)
    if len(close) < slow_span:
        return "uncertain"
    fast = ema(close, fast_span).iloc[-1]
    slow = ema(close, slow_span).iloc[-1]
    price = close.iloc[-1]
    if price > slow and fast > slow:
        return "bullish"
    if price < slow and fast < slow:
        return "bearish"
    return "sideways"
