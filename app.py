import pandas as pd
import streamlit as st

from src.data.providers import default_symbols
from src.data.yfinance_provider import YFinanceProvider
from src.strategies.scanner import scan_symbol


APP_TITLE = "Trading Signal Scanner"
THEME_ACCENT = "#f97316"


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
        st.markdown('<div class="signal-card">', unsafe_allow_html=True)
        st.write("Razones:", ", ".join(signal.reasons))
        st.write(f"Entrada: {signal.entry} | SL: {signal.stop_loss} | TP: {signal.take_profit}")
        st.write(f"Direccion: {signal.direction.value} | Score: {signal.score}% | R:R: {signal.risk_reward}")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No hay oportunidades que superen el filtro actual.")

    if errors:
        with st.expander("Errores de datos"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
