from app import APP_TITLE, THEME_ACCENT, chart_period_for_interval, evaluation_rows
from app import journal_rows
from src.evaluation.historical import StrategyEvaluation
from src.journal.models import JournalStatus, RecommendationRecord
from datetime import datetime, timezone


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


def test_journal_rows_formats_records_for_table():
    record = RecommendationRecord(
        signal_key="key",
        created_at=datetime(2026, 5, 29, tzinfo=timezone.utc),
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction="LONG",
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=("ORDER BLOCK",),
        reasons=("valid order block",),
        status=JournalStatus.TP,
        outcome_r=2.0,
        resolution_note="TP touched before SL",
    )

    rows = journal_rows([record])

    assert rows[0]["Symbol"] == "EUR/USD"
    assert rows[0]["Status"] == "TP"
    assert rows[0]["Outcome R"] == 2.0
