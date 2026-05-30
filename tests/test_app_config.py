from app import APP_TITLE, THEME_ACCENT, chart_period_for_interval, evaluation_rows
from app import journal_rows, scan_symbol_items, scanner_scan_key
from app import command_center_header_html, command_metric_card, plotly_chart_config
from app import strategy_option_label, strategy_profile_from_label
from src.evaluation.historical import StrategyEvaluation
from src.journal.models import JournalStatus, RecommendationRecord
from src.models.signals import Direction, SignalCandidate
from datetime import datetime, timezone


def test_app_uses_dark_orange_identity():
    assert APP_TITLE == "Trading Signal Scanner"
    assert THEME_ACCENT == "#f97316"


def test_command_center_helpers_render_distinct_ui_classes():
    header = command_center_header_html()
    card = command_metric_card("Senales", 5, "green", "Activas")

    assert "command-header" in header
    assert "LIVE MARKET COMMAND CENTER" in header
    assert "command-metric green" in card
    assert "Senales" in card
    assert "Activas" in card


def test_chart_period_for_interval_uses_max_for_daily_and_limited_for_intraday():
    assert chart_period_for_interval("1d") == "max"
    assert chart_period_for_interval("1wk") == "max"
    assert chart_period_for_interval("1h") == "730d"


def test_plotly_chart_config_enables_mouse_wheel_zoom():
    config = plotly_chart_config()

    assert config["scrollZoom"] is True
    assert config["displayModeBar"] is True
    assert config["responsive"] is True


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


def test_strategy_option_label_includes_win_rate():
    label = strategy_option_label(
        "Order Block",
        [
            StrategyEvaluation(
                profile="Order Block",
                setups=25,
                wins=10,
                losses=15,
                win_rate=40.0,
                profit_factor=1.3,
                average_r=0.2,
                max_drawdown=0.08,
            )
        ],
    )

    assert label == "Order Block (40.0%)"


def test_strategy_profile_from_label_strips_visible_percent():
    assert strategy_profile_from_label("Order Block (40.0%)") == "Order Block"
    assert strategy_profile_from_label("Senal combinada") == "Senal combinada"


def test_scan_symbol_items_sorts_results_and_collects_errors(monkeypatch):
    def fake_scan_symbol_item(display_symbol, provider_symbol, timeframe, account_balance, min_score):
        if display_symbol == "Bad":
            raise ValueError("boom")
        score = 90 if display_symbol == "High" else 75
        return SignalCandidate(
            symbol=provider_symbol,
            display_symbol=display_symbol,
            direction=Direction.LONG,
            timeframe=timeframe,
            entry=1.0,
            stop_loss=0.9,
            take_profit=1.2,
            score=score,
            risk_reward=2.0,
            strategy_tags=("TREND",),
            reasons=("trend aligned",),
        )

    monkeypatch.setattr("app.scan_symbol_item", fake_scan_symbol_item)

    signals, errors = scan_symbol_items(
        (("Low", "LOW"), ("Bad", "BAD"), ("High", "HIGH")),
        timeframe="1h",
        account_balance=10_000,
        min_score=70,
        max_workers=3,
    )

    assert [signal.display_symbol for signal in signals] == ["High", "Low"]
    assert errors == ("Bad: boom",)


def test_scanner_scan_key_rounds_account_balance():
    key = scanner_scan_key((("EUR/USD", "EURUSD=X"),), "1h", 10000.129, 70)

    assert key == ((("EUR/USD", "EURUSD=X"),), "1h", 10000.13, 70)


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
        entry_triggered_at=datetime(2026, 5, 29, 1, tzinfo=timezone.utc),
        outcome_r=2.0,
        resolution_note="TP touched before SL",
        feedback="TP alcanzado.",
    )

    rows = journal_rows([record])

    assert rows[0]["Symbol"] == "EUR/USD"
    assert rows[0]["Entry Triggered"] == "2026-05-29 01:00"
    assert rows[0]["Status"] == "TP"
    assert rows[0]["Outcome R"] == 2.0
    assert rows[0]["Feedback"] == "TP alcanzado."
