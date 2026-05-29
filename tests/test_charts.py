import pandas as pd

from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.models.signals import Direction


def sample_ohlcv() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [102.0, 103.0, 104.0],
            "low": [99.0, 100.0, 101.0],
            "close": [101.0, 102.0, 103.0],
            "volume": [1000, 1100, 1200],
        },
        index=pd.date_range("2026-01-01", periods=3, freq="D"),
    )


def test_build_candlestick_figure_contains_candles_and_trade_levels():
    levels = TradeLevels(entry=103.0, stop_loss=100.0, take_profit=109.0, direction=Direction.LONG)

    fig = build_candlestick_figure(sample_ohlcv(), levels, "EUR/USD", ("Order Block", "FVG"))

    assert len(fig.data) >= 2
    assert fig.data[0].type == "candlestick"
    assert any(shape["line"]["color"] == "#ef4444" for shape in fig.layout.shapes)
    assert any(shape["line"]["color"] == "#22c55e" for shape in fig.layout.shapes)


def test_trade_levels_marker_has_entry_price():
    levels = TradeLevels(entry=103.0, stop_loss=100.0, take_profit=109.0, direction=Direction.LONG)

    fig = build_candlestick_figure(sample_ohlcv(), levels, "EUR/USD", ("Trend Alignment",))

    entry_trace = fig.data[1]
    assert entry_trace.name == "Entry"
    assert entry_trace.y[0] == 103.0


def test_chart_history_note_marks_intraday_as_limited():
    assert "limited" in chart_history_note("1h").lower()
    assert "maximum" in chart_history_note("1d").lower()
