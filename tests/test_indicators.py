import pandas as pd

from src.indicators.momentum import ema_cross_direction, rsi
from src.indicators.trend import ema, trend_regime
from src.indicators.volatility import atr


def test_ema_returns_series_same_length():
    series = pd.Series([1, 2, 3, 4, 5], dtype=float)

    result = ema(series, span=3)

    assert len(result) == 5
    assert result.iloc[-1] > result.iloc[0]


def test_trend_regime_bullish_when_fast_above_slow():
    df = pd.DataFrame({"close": list(range(1, 260))})

    result = trend_regime(df, fast_span=10, slow_span=30)

    assert result == "bullish"


def test_rsi_stays_between_zero_and_one_hundred():
    values = pd.Series([1, 2, 3, 2, 4, 5, 4, 6, 7, 6, 8, 9, 10, 9, 11], dtype=float)

    result = rsi(values, period=5).dropna()

    assert result.between(0, 100).all()


def test_ema_cross_direction_detects_long_cross():
    fast = pd.Series([1.0, 1.0, 3.0])
    slow = pd.Series([2.0, 2.0, 2.0])

    assert ema_cross_direction(fast, slow) == "long"


def test_atr_uses_true_range():
    df = pd.DataFrame(
        {
            "high": [10.0, 12.0, 13.0],
            "low": [8.0, 9.0, 10.0],
            "close": [9.0, 11.0, 12.0],
        }
    )

    result = atr(df, period=2)

    assert result.iloc[-1] > 0
