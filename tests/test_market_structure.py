import pandas as pd

from src.indicators.imbalance import fair_value_gaps
from src.indicators.structure import latest_structure_break, swing_points
from src.strategies.liquidity import liquidity_sweep
from src.strategies.order_blocks import order_block_candidates


def test_swing_points_marks_local_extremes():
    df = pd.DataFrame(
        {
            "high": [1, 3, 2, 4, 2],
            "low": [0, 1, 1, 1, 0],
            "close": [1, 2, 2, 3, 1],
        }
    )

    swings = swing_points(df, window=1)

    assert swings["swing_high"].sum() == 2


def test_latest_structure_break_detects_bullish_break():
    df = pd.DataFrame(
        {
            "high": [1, 3, 2, 2.5, 3.5],
            "low": [0.5, 1, 1, 1.5, 2],
            "close": [0.9, 2.5, 2.0, 2.2, 3.4],
        }
    )

    assert latest_structure_break(df, window=1) == "bullish_bos"


def test_fair_value_gap_detects_bullish_gap():
    df = pd.DataFrame(
        {
            "high": [10.0, 11.0, 13.0],
            "low": [9.0, 10.5, 12.0],
            "close": [9.5, 10.8, 12.5],
        }
    )

    gaps = fair_value_gaps(df)

    assert gaps.iloc[-1]["type"] == "bullish"


def test_order_block_candidate_detects_bullish_impulse():
    df = pd.DataFrame(
        {
            "open": [10.0, 9.8, 10.2, 11.5],
            "high": [10.1, 10.0, 11.0, 12.5],
            "low": [9.7, 9.5, 10.0, 11.0],
            "close": [9.8, 9.6, 10.9, 12.2],
            "volume": [100, 120, 200, 250],
        }
    )

    blocks = order_block_candidates(df, impulse_multiplier=1.2)

    assert blocks[-1]["direction"] == "long"


def test_liquidity_sweep_detects_rejection_above_equal_highs():
    df = pd.DataFrame(
        {
            "high": [10.0, 10.02, 10.5],
            "low": [9.5, 9.7, 9.8],
            "close": [9.8, 9.9, 9.95],
        }
    )

    assert liquidity_sweep(df, tolerance=0.05) == "bearish_sweep"
