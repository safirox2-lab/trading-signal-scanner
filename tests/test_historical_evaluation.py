import pandas as pd

from src.evaluation.historical import (
    StrategyEvaluation,
    _trade_outcome_from_arrays,
    evaluate_static_setups,
    evaluate_strategy_profiles,
    latest_trade_levels_for_profile,
    simulate_trade_outcome,
)
from src.models.signals import Direction


def test_simulate_trade_outcome_counts_take_profit_first_as_win():
    future = pd.DataFrame({"high": [104.0, 111.0], "low": [99.0, 103.0]})

    result = simulate_trade_outcome(future, Direction.LONG, entry=100.0, stop_loss=95.0, take_profit=110.0)

    assert result == 2.0


def test_simulate_trade_outcome_counts_same_candle_touch_as_loss():
    future = pd.DataFrame({"high": [111.0], "low": [94.0]})

    result = simulate_trade_outcome(future, Direction.LONG, entry=100.0, stop_loss=95.0, take_profit=110.0)

    assert result == -1.0


def test_simulate_trade_outcome_counts_short_same_candle_touch_as_loss():
    future = pd.DataFrame({"high": [106.0], "low": [88.0]})

    result = simulate_trade_outcome(future, Direction.SHORT, entry=100.0, stop_loss=105.0, take_profit=90.0)

    assert result == -1.0


def test_trade_outcome_from_arrays_checks_stop_before_target():
    result = _trade_outcome_from_arrays([111.0], [94.0], Direction.LONG, entry=100.0, stop_loss=95.0, take_profit=110.0)

    assert result == -1.0


def test_evaluate_strategy_profiles_returns_all_profiles_after_optimization():
    df = pd.DataFrame(
        {
            "open": [100, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112] * 8,
            "high": [102, 104, 105, 103, 107, 108, 106, 110, 111, 109, 114, 115] * 8,
            "low": [99, 100, 102, 100, 103, 104, 102, 106, 108, 105, 109, 111] * 8,
            "close": [101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 114] * 8,
            "volume": [1000, 1200, 900, 1500, 2000, 1000, 2500, 1100, 1300, 2600, 1400, 2800] * 8,
        }
    )

    evaluations = evaluate_strategy_profiles(df, Direction.LONG)

    assert [item.profile for item in evaluations] == [
        "Scalping / EMA Momentum",
        "Order Block",
        "FVG / Imbalance",
        "Liquidity Sweep",
        "Trend Alignment",
    ]


def test_evaluate_static_setups_reports_win_rate_and_profit_factor():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102, 103, 104, 105],
            "high": [101, 106, 111, 106, 116, 117],
            "low": [99, 100, 101, 102, 103, 104],
            "close": [100, 105, 110, 105, 111, 112],
            "volume": [1000] * 6,
        }
    )
    setup_indexes = [0, 3]

    evaluation = evaluate_static_setups(df, Direction.LONG, setup_indexes, reward_multiple=2.0, stop_distance=5.0)

    assert isinstance(evaluation, StrategyEvaluation)
    assert evaluation.setups == 2
    assert evaluation.win_rate == 100.0
    assert evaluation.profit_factor == float("inf")


def test_evaluate_strategy_profiles_uses_distinct_setups_and_risk():
    df = pd.DataFrame(
        {
            "open": [100, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112],
            "high": [102, 104, 105, 103, 107, 108, 106, 110, 111, 109, 114, 115],
            "low": [99, 100, 102, 100, 103, 104, 102, 106, 108, 105, 109, 111],
            "close": [101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 114],
            "volume": [1000, 1200, 900, 1500, 2000, 1000, 2500, 1100, 1300, 2600, 1400, 2800],
        }
    )

    evaluations = evaluate_strategy_profiles(df, Direction.LONG)
    setup_counts = {item.profile: item.setups for item in evaluations}
    win_rates = {item.win_rate for item in evaluations}

    assert setup_counts["Scalping / EMA Momentum"] != setup_counts["Order Block"]
    assert len(win_rates) > 1


def test_latest_trade_levels_for_profile_returns_profile_specific_levels():
    df = pd.DataFrame(
        {
            "open": [100, 101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112] * 6,
            "high": [102, 104, 105, 103, 107, 108, 106, 110, 111, 109, 114, 115] * 6,
            "low": [99, 100, 102, 100, 103, 104, 102, 106, 108, 105, 109, 111] * 6,
            "close": [101, 103, 102, 104, 106, 105, 107, 109, 108, 110, 112, 114] * 6,
            "volume": [1000, 1200, 900, 1500, 2000, 1000, 2500, 1100, 1300, 2600, 1400, 2800] * 6,
        }
    )

    scalping = latest_trade_levels_for_profile(df, Direction.LONG, "Scalping / EMA Momentum")
    trend = latest_trade_levels_for_profile(df, Direction.LONG, "Trend Alignment")

    assert scalping is not None
    assert trend is not None
    assert scalping.take_profit != trend.take_profit
    assert scalping.stop_loss != trend.stop_loss
