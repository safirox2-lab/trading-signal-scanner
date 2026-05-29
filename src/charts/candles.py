from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from src.models.signals import Direction


@dataclass(frozen=True)
class TradeLevels:
    entry: float
    stop_loss: float
    take_profit: float
    direction: Direction


def chart_history_note(interval: str) -> str:
    if interval.endswith("m") or interval.endswith("h"):
        return "Intraday/scalping history is limited by provider availability."
    return "Using maximum practical historical depth available from the provider."


def build_candlestick_figure(
    df: pd.DataFrame,
    levels: TradeLevels,
    title: str,
    strategy_tags: tuple[str, ...],
) -> go.Figure:
    candles = df.copy()
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=candles.index,
            open=candles["open"],
            high=candles["high"],
            low=candles["low"],
            close=candles["close"],
            name="Candles",
            increasing_line_color="#22c55e",
            decreasing_line_color="#ef4444",
        )
    )
    marker_color = "#f97316" if levels.direction == Direction.LONG else "#ef4444"
    fig.add_trace(
        go.Scatter(
            x=[candles.index[-1]],
            y=[levels.entry],
            mode="markers+text",
            marker={"size": 13, "color": marker_color, "symbol": "circle"},
            text=["Entry"],
            textposition="top center",
            name="Entry",
        )
    )
    fig.add_hline(y=levels.stop_loss, line_color="#ef4444", line_width=2, annotation_text="SL")
    fig.add_hline(y=levels.take_profit, line_color="#22c55e", line_width=2, annotation_text="TP")
    fig.update_layout(
        title=f"{title} - {levels.direction.value} | {', '.join(strategy_tags)}",
        template="plotly_dark",
        paper_bgcolor="#0f1117",
        plot_bgcolor="#0f1117",
        font={"color": "#f3f4f6"},
        xaxis_rangeslider_visible=False,
        height=560,
        margin={"l": 10, "r": 10, "t": 60, "b": 10},
    )
    return fig
