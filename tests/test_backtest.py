import pandas as pd

from src.backtest.engine import backtest_static_plan
from src.backtest.metrics import max_drawdown, summarize_trades
from src.models.signals import Direction


def test_max_drawdown_detects_drop_from_peak():
    assert max_drawdown([100, 120, 90, 130]) == 0.25


def test_summarize_trades_calculates_win_rate():
    summary = summarize_trades([2.0, -1.0, 2.0])

    assert summary["trades"] == 3
    assert round(summary["win_rate"], 2) == 66.67
    assert summary["profit_factor"] == 4.0


def test_backtest_static_plan_closes_at_take_profit():
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [101, 111, 112],
            "low": [99, 100, 101],
            "close": [100, 110, 111],
            "volume": [1000, 1000, 1000],
        }
    )

    result = backtest_static_plan(df, Direction.LONG, entry=100, stop_loss=95, take_profit=110, initial_balance=10_000)

    assert result["final_balance"] > 10_000
    assert result["trades"] == 1
