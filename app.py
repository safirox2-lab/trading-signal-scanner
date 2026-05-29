import pandas as pd
import streamlit as st

from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.data.providers import default_symbols
from src.data.yfinance_provider import YFinanceProvider
from src.evaluation.historical import StrategyEvaluation, evaluate_static_setups
from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.strategies.scanner import scan_symbol


APP_TITLE = "Trading Signal Scanner"
THEME_ACCENT = "#f97316"
STRATEGY_PROFILES = (
    "Scalping / EMA Momentum",
    "Order Block",
    "FVG / Imbalance",
    "Liquidity Sweep",
    "Trend Alignment",
)


def chart_period_for_interval(interval: str) -> str:
    if interval in {"1d", "1wk"}:
        return "max"
    return "730d"


def evaluation_rows(
    evaluations: list[StrategyEvaluation],
    supported_profiles: tuple[str, ...],
) -> list[dict[str, str | int | float]]:
    rows = []
    for evaluation in evaluations:
        rows.append(
            {
                "Strategy profile": evaluation.profile,
                "Supports current trade": "Yes" if evaluation.profile in supported_profiles else "No",
                "Historical setups": evaluation.setups,
                "Win rate": f"{evaluation.win_rate:.1f}%",
                "Profit factor": evaluation.profit_factor,
                "Average R": evaluation.average_r,
                "Max drawdown": f"{evaluation.max_drawdown * 100:.1f}%",
            }
        )
    return rows


@st.cache_data(show_spinner=False, ttl=900)
def load_history(symbol: str, period: str, interval: str) -> pd.DataFrame:
    return YFinanceProvider().history(symbol, period=period, interval=interval)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #0f1117; color: #f3f4f6; }
        [data-testid="stSidebar"] { background: #151923; }
        h1, h2, h3 { color: #f97316; }
        div[data-testid="stMetricValue"] { color: #fb923c; }
        .signal-card {
            background: #151923;
            border: 1px solid #272b35;
            border-radius: 8px;
            padding: 14px;
        }
        .disclaimer {
            color: #d1d5db;
            background: #1f2530;
            border-left: 4px solid #f97316;
            padding: 10px 12px;
            border-radius: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def signals_to_frame(signals) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Symbol": signal.display_symbol,
                "Direction": signal.direction.value,
                "Score": signal.score,
                "Entry": signal.entry,
                "Stop Loss": signal.stop_loss,
                "Take Profit": signal.take_profit,
                "R:R": signal.risk_reward,
                "Timeframe": signal.timeframe,
                "Strategy": ", ".join(signal.strategy_tags),
            }
            for signal in signals
        ]
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    apply_theme()
    st.title(APP_TITLE)
    st.markdown(
        '<div class="disclaimer">Herramienta educativa/de analisis. No es asesoria financiera ni garantia de ganancia.</div>',
        unsafe_allow_html=True,
    )

    provider = YFinanceProvider()
    symbols = default_symbols()

    with st.sidebar:
        st.header("Filtros")
        selected_markets = st.multiselect(
            "Mercados",
            sorted({symbol.market for symbol in symbols}),
            default=["forex", "indices", "commodities"],
        )
        timeframe = st.selectbox("Timeframe", ["1h", "1d"], index=0)
        min_score = st.slider("Score minimo", min_value=0, max_value=100, value=70, step=5)
        account_balance = st.number_input("Capital de cuenta", min_value=100.0, value=10_000.0, step=100.0)

    selected_symbols = [symbol for symbol in symbols if symbol.market in selected_markets]
    signals = []
    errors = []
    for symbol in selected_symbols:
        try:
            signal = scan_symbol(
                provider=provider,
                display_symbol=symbol.display,
                provider_symbol=symbol.provider_symbol,
                timeframe=timeframe,
                account_balance=account_balance,
                min_score=min_score,
            )
            if signal:
                signals.append(signal)
        except Exception as exc:
            errors.append(f"{symbol.display}: {exc}")

    signals = sorted(signals, key=lambda item: item.score, reverse=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Senales", len(signals))
    col2.metric("Score minimo", f"{min_score}%")
    col3.metric("Riesgo", "1%")
    col4.metric("Mercados", len(selected_symbols))

    st.subheader("Oportunidades")
    if signals:
        st.dataframe(signals_to_frame(signals), use_container_width=True, hide_index=True)
        selected = st.selectbox("Detalle de senal", [signal.display_symbol for signal in signals])
        signal = next(item for item in signals if item.display_symbol == selected)
        supported_profiles = classify_strategy_profiles(signal)
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        st.write("Razones:", ", ".join(signal.reasons))
        st.write(f"Entrada: {signal.entry} | SL: {signal.stop_loss} | TP: {signal.take_profit}")
        st.write(f"Direccion: {signal.direction.value} | Score: {signal.score}% | R:R: {signal.risk_reward}")
        st.write(f"Estrategias a favor: {len(supported_profiles)} - {', '.join(supported_profiles)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.subheader("Grafico y niveles de trade")
        chart_interval = st.selectbox("Intervalo del grafico", ["1h", "1d", "1wk"], index=1)
        chart_period = chart_period_for_interval(chart_interval)
        st.caption(chart_history_note(chart_interval))
        try:
            chart_df = load_history(signal.symbol, period=chart_period, interval=chart_interval)
            levels = TradeLevels(
                entry=signal.entry,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
                direction=signal.direction,
            )
            fig = build_candlestick_figure(chart_df.tail(240), levels, signal.display_symbol, supported_profiles)
            st.plotly_chart(fig, use_container_width=True)

            setup_indexes = list(range(20, max(20, len(chart_df) - 5), 20))
            evaluations = [
                evaluate_static_setups(chart_df, signal.direction, setup_indexes, profile=profile)
                for profile in STRATEGY_PROFILES
            ]
            supported = [item for item in evaluations if item.profile in supported_profiles and item.setups > 0]
            combined_win_rate = sum(item.win_rate for item in supported) / len(supported) if supported else 0.0
            combined_setups = sum(item.setups for item in supported)
            st.subheader("Evaluacion historica de estrategias")
            st.write(confluence_summary(signal, combined_win_rate, combined_setups))
            st.dataframe(evaluation_rows(evaluations, supported_profiles), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"No se pudo cargar el grafico/evaluacion historica: {exc}")
    else:
        st.info("No hay oportunidades que superen el filtro actual.")

    if errors:
        with st.expander("Errores de datos"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
