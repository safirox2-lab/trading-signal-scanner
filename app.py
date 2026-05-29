from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import streamlit as st

from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.data.providers import default_symbols
from src.data.yfinance_provider import YFinanceProvider
from src.evaluation.historical import StrategyEvaluation, evaluate_strategy_profiles, latest_trade_levels_for_profile
from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.journal.metrics import hit_rate_by_strategy, hit_rate_by_symbol, journal_summary
from src.journal.models import JournalStatus, RecommendationRecord, record_from_signal
from src.journal.resolver import resolve_recommendation
from src.journal.store import JournalStore
from src.models.signals import Direction
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


@st.cache_data(show_spinner=False, ttl=900)
def cached_strategy_evaluations(
    symbol: str,
    period: str,
    interval: str,
    direction_value: str,
) -> list[StrategyEvaluation]:
    chart_df = load_history(symbol, period=period, interval=interval)
    return evaluate_strategy_profiles(chart_df, Direction(direction_value))


@st.cache_data(show_spinner=False, ttl=900)
def cached_profile_trade_levels(
    symbol: str,
    period: str,
    interval: str,
    direction_value: str,
    profile: str,
):
    chart_df = load_history(symbol, period=period, interval=interval)
    return latest_trade_levels_for_profile(chart_df, Direction(direction_value), profile)


@st.cache_data(show_spinner=False, ttl=900)
def cached_candlestick_figure(
    symbol: str,
    period: str,
    interval: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    direction_value: str,
    title: str,
    strategy_tags: tuple[str, ...],
):
    chart_df = load_history(symbol, period=period, interval=interval)
    levels = TradeLevels(
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        direction=Direction(direction_value),
    )
    return build_candlestick_figure(chart_df.tail(240), levels, title, strategy_tags)


@st.cache_data(show_spinner=False, ttl=900)
def cached_scan_symbols(
    symbol_items: tuple[tuple[str, str], ...],
    timeframe: str,
    account_balance: float,
    min_score: int,
):
    return scan_symbol_items(symbol_items, timeframe, account_balance, min_score)


def scan_symbol_item(
    display_symbol: str,
    provider_symbol: str,
    timeframe: str,
    account_balance: float,
    min_score: int,
):
    provider = YFinanceProvider()
    return scan_symbol(
        provider=provider,
        display_symbol=display_symbol,
        provider_symbol=provider_symbol,
        timeframe=timeframe,
        account_balance=account_balance,
        min_score=min_score,
    )


def scan_symbol_items(
    symbol_items: tuple[tuple[str, str], ...],
    timeframe: str,
    account_balance: float,
    min_score: int,
    max_workers: int = 5,
):
    signals = []
    errors = []
    if not symbol_items:
        return (), ()

    worker_count = min(max_workers, len(symbol_items))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(
                scan_symbol_item,
                display_symbol,
                provider_symbol,
                timeframe,
                account_balance,
                min_score,
            ): display_symbol
            for display_symbol, provider_symbol in symbol_items
        }
        for future in as_completed(futures):
            display_symbol = futures[future]
            try:
                signal = future.result()
                if signal:
                    signals.append(signal)
            except Exception as exc:
                errors.append(f"{display_symbol}: {exc}")
    return tuple(sorted(signals, key=lambda item: item.score, reverse=True)), tuple(errors)


def stored_scanner_results(scan_key):
    if st.session_state.get("scanner_scan_key") != scan_key:
        return (), ()
    return (
        st.session_state.get("scanner_signals", ()),
        st.session_state.get("scanner_errors", ()),
    )


def save_scanner_results(scan_key, signals, errors) -> None:
    st.session_state["scanner_scan_key"] = scan_key
    st.session_state["scanner_signals"] = signals
    st.session_state["scanner_errors"] = errors


def scanner_scan_key(
    symbol_items: tuple[tuple[str, str], ...],
    timeframe: str,
    account_balance: float,
    min_score: int,
):
    return (
        symbol_items,
        timeframe,
        round(account_balance, 2),
        min_score,
    )


def scan_controls(
    symbol_items: tuple[tuple[str, str], ...],
    timeframe: str,
    account_balance: float,
    min_score: int,
    auto_scan: bool,
    scan_now: bool,
):
    scan_key = scanner_scan_key(symbol_items, timeframe, account_balance, min_score)
    if auto_scan or scan_now:
        with st.spinner("Escaneando mercados..."):
            signals, errors = cached_scan_symbols(
                symbol_items,
                timeframe,
                account_balance,
                min_score,
            )
        save_scanner_results(scan_key, signals, errors)
        return signals, errors
    return stored_scanner_results(scan_key)


def strategy_option_label(profile: str, evaluations: list[StrategyEvaluation]) -> str:
    if profile == "Senal combinada":
        return profile
    by_profile = {evaluation.profile: evaluation for evaluation in evaluations}
    evaluation = by_profile.get(profile)
    if not evaluation or evaluation.setups == 0:
        return f"{profile} (sin datos)"
    return f"{profile} ({evaluation.win_rate:.1f}%)"


def strategy_profile_from_label(label: str) -> str:
    return label.split(" (", 1)[0]


def journal_rows(records: list[RecommendationRecord]) -> list[dict[str, str | int | float | None]]:
    return [
        {
            "Created": record.created_at.strftime("%Y-%m-%d %H:%M"),
            "Symbol": record.display_symbol,
            "Direction": record.direction,
            "Entry": record.entry,
            "SL": record.stop_loss,
            "TP": record.take_profit,
            "Score": record.score,
            "Strategies": ", ".join(record.strategy_tags),
            "Status": record.status.value,
            "Outcome R": record.outcome_r,
            "Note": record.resolution_note,
        }
        for record in records
    ]


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
        auto_record = st.toggle("Registrar recomendaciones automaticamente", value=False)
        auto_scan = st.toggle("Escanear al abrir", value=False)
        scan_now = st.button("Buscar oportunidades", type="primary")
        if st.button("Actualizar datos ahora"):
            st.cache_data.clear()
            st.session_state["scanner_force_scan"] = True
            st.rerun()

    selected_symbols = [symbol for symbol in symbols if symbol.market in selected_markets]
    symbol_items = tuple((symbol.display, symbol.provider_symbol) for symbol in selected_symbols)
    scan_key = scanner_scan_key(symbol_items, timeframe, account_balance, min_score)
    force_scan = st.session_state.pop("scanner_force_scan", False)
    signals, errors = scan_controls(
        symbol_items,
        timeframe,
        account_balance,
        min_score,
        auto_scan,
        scan_now or force_scan,
    )
    has_current_scan = st.session_state.get("scanner_scan_key") == scan_key
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Senales", len(signals))
    col2.metric("Score minimo", f"{min_score}%")
    col3.metric("Riesgo", "1%")
    col4.metric("Mercados", len(selected_symbols))

    store = JournalStore()
    if auto_record:
        inserted = 0
        for signal in signals:
            if store.insert_recommendation(record_from_signal(signal)):
                inserted += 1
        if inserted:
            st.toast(f"Recomendaciones registradas: {inserted}")

    scanner_tab, journal_tab = st.tabs(["Scanner", "Registro autonomo"])

    with scanner_tab:
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
                evaluations = cached_strategy_evaluations(
                    signal.symbol,
                    chart_period,
                    chart_interval,
                    signal.direction.value,
                )
                strategy_options = ("Senal combinada",) + STRATEGY_PROFILES
                strategy_labels = tuple(strategy_option_label(profile, evaluations) for profile in strategy_options)
                strategy_chart_choice = st.selectbox(
                    "Estrategia en grafico",
                    strategy_labels,
                )
                strategy_chart_choice = strategy_profile_from_label(strategy_chart_choice)
                profile_levels = None
                if strategy_chart_choice != "Senal combinada":
                    profile_levels = cached_profile_trade_levels(
                        signal.symbol,
                        chart_period,
                        chart_interval,
                        signal.direction.value,
                        strategy_chart_choice,
                    )
                if profile_levels:
                    levels = TradeLevels(
                        entry=profile_levels.entry,
                        stop_loss=profile_levels.stop_loss,
                        take_profit=profile_levels.take_profit,
                        direction=signal.direction,
                    )
                    chart_tags = (profile_levels.profile,)
                    st.write(
                        f"{profile_levels.profile}: Entrada {profile_levels.entry} | "
                        f"SL {profile_levels.stop_loss} | TP {profile_levels.take_profit} | "
                        f"R:R {profile_levels.risk_reward}"
                    )
                else:
                    levels = TradeLevels(
                        entry=signal.entry,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit,
                        direction=signal.direction,
                    )
                    chart_tags = supported_profiles
                    if strategy_chart_choice != "Senal combinada":
                        st.warning("La estrategia seleccionada no tiene setup reciente suficiente para marcar niveles.")
                fig = cached_candlestick_figure(
                    signal.symbol,
                    chart_period,
                    chart_interval,
                    levels.entry,
                    levels.stop_loss,
                    levels.take_profit,
                    signal.direction.value,
                    signal.display_symbol,
                    chart_tags,
                )
                st.plotly_chart(fig, use_container_width=True)

                supported = [item for item in evaluations if item.profile in supported_profiles and item.setups > 0]
                combined_win_rate = sum(item.win_rate for item in supported) / len(supported) if supported else 0.0
                combined_setups = sum(item.setups for item in supported)
                st.subheader("Evaluacion historica de estrategias")
                st.write(confluence_summary(signal, combined_win_rate, combined_setups))
                st.dataframe(evaluation_rows(evaluations, supported_profiles), use_container_width=True, hide_index=True)
            except Exception as exc:
                st.warning(f"No se pudo cargar el grafico/evaluacion historica: {exc}")
        else:
            if has_current_scan:
                st.info("No hay oportunidades que superen el filtro actual.")
            else:
                st.info("Scanner listo para buscar oportunidades.")

    with journal_tab:
        st.subheader("Registro autonomo")
        st.caption(
            "Este registro mide resultados historicos de recomendaciones guardadas. "
            "En Streamlit Cloud, el registro local puede reiniciarse; para persistencia real conecta Supabase/Postgres."
        )
        if st.button("Actualizar recomendaciones abiertas"):
            updated_count = 0
            for record in store.list_recommendations():
                if record.status != JournalStatus.OPEN:
                    continue
                try:
                    history = load_history(record.symbol, period="730d", interval=record.timeframe)
                    updated = resolve_recommendation(record, history)
                    if updated.status != record.status and updated.outcome_r is not None:
                        store.update_resolution(
                            record.signal_key,
                            updated.status,
                            updated.outcome_r,
                            updated.resolution_note,
                            updated.resolved_at,
                        )
                        updated_count += 1
                except Exception as exc:
                    st.warning(f"No se pudo evaluar {record.display_symbol}: {exc}")
            st.success(f"Recomendaciones actualizadas: {updated_count}")

        records = store.list_recommendations()
        summary = journal_summary(records)
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total", summary["total"])
        m2.metric("TP", summary["wins"])
        m3.metric("SL", summary["losses"])
        m4.metric("Abiertas", summary["open"])
        m5.metric("% acierto", f'{summary["hit_rate"]:.1f}%')
        st.metric("Average R", summary["average_r"])

        if records:
            statuses = ["ALL"] + sorted({record.status.value for record in records})
            selected_status = st.selectbox("Filtrar estado", statuses)
            filtered = records if selected_status == "ALL" else [
                record for record in records if record.status.value == selected_status
            ]
            st.dataframe(journal_rows(filtered), use_container_width=True, hide_index=True)

            st.subheader("Acierto por estrategia")
            st.dataframe(hit_rate_by_strategy(records), use_container_width=True, hide_index=True)

            st.subheader("Acierto por simbolo")
            st.dataframe(hit_rate_by_symbol(records), use_container_width=True, hide_index=True)
        else:
            st.info("Aun no hay recomendaciones registradas.")

    if errors:
        with st.expander("Errores de datos"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
