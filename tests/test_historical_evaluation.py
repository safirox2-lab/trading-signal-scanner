import pandas as pd

from src.evaluation.historical import (
    StrategyEvaluation,
    evaluate_static_setups,
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
