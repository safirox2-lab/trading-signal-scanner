from app import APP_TITLE, THEME_ACCENT, chart_period_for_interval, evaluation_rows
from src.evaluation.historical import StrategyEvaluation


def test_app_uses_dark_orange_identity():
    assert APP_TITLE == "Trading Signal Scanner"
    assert THEME_ACCENT == "#f97316"


def test_chart_period_for_interval_uses_max_for_daily_and_limited_for_intraday():
    assert chart_period_for_interval("1d") == "max"
    assert chart_period_for_interval("1wk") == "max"
    assert chart_period_for_interval("1h") == "730d"


def test_evaluation_rows_formats_percentages():
    rows = evaluation_rows(
        [
            StrategyEvaluation(
                profile="Order Block",
                setups=10,
                wins=6,
                losses=4,
                win_rate=60.0,
                profit_factor=3.0,
                average_r=0.8,
                max_drawdown=0.12,
            )
        ],
        supported_profiles=("Order Block",),
    )

    assert rows[0]["Supports current trade"] == "Yes"
    assert rows[0]["Win rate"] == "60.0%"
    assert rows[0]["Max drawdown"] == "12.0%"
