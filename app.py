from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import escape

import pandas as pd
import plotly.io as pio
import streamlit as st

from src.charts.candles import TradeLevels, build_candlestick_figure, chart_history_note
from src.data.providers import default_symbols
from src.data.yfinance_provider import YFinanceProvider
from src.evaluation.historical import StrategyEvaluation, evaluate_strategy_profiles, latest_trade_levels_for_profile
from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.journal.chart_snapshots import ChartSnapshotRecord, chart_snapshot_key, entry_changed, same_snapshot_context
from src.journal.metrics import hit_rate_by_strategy, hit_rate_by_symbol, journal_summary, strategy_feedback_rows
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


def plotly_chart_config() -> dict[str, bool]:
    return {
        "scrollZoom": True,
        "displayModeBar": True,
        "responsive": True,
    }


def command_center_header_html() -> str:
    return """
    <div class="command-header">
        <div>
            <div class="eyebrow">LIVE MARKET COMMAND CENTER</div>
            <div class="command-title">Trading Signal Scanner</div>
            <div class="command-subtitle">Scanner tecnico, registro autonomo y feedback historico de estrategias.</div>
        </div>
        <div class="command-pills">
            <span>Buscar</span>
            <span>Registro</span>
            <span>Feedback</span>
        </div>
    </div>
    """


def command_metric_card(label: str, value: str | int | float, tone: str = "orange", detail: str = "") -> str:
    detail_html = f'<div class="metric-detail">{escape(str(detail))}</div>' if detail else ""
    return (
        f'<div class="command-metric {escape(tone)}">'
        f'<div class="metric-label">{escape(str(label))}</div>'
        f'<div class="metric-value">{escape(str(value))}</div>'
        f"{detail_html}"
        "</div>"
    )


def section_header_html(title: str, subtitle: str = "") -> str:
    subtitle_html = f'<div class="section-subtitle">{escape(subtitle)}</div>' if subtitle else ""
    return f'<div class="section-heading"><h2>{escape(title)}</h2>{subtitle_html}</div>'


def chart_snapshot_metadata(
    symbol: str,
    interval: str,
    period: str,
    strategy: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    direction: str,
) -> dict[str, str | float]:
    return {
        "symbol": symbol,
        "interval": interval,
        "period": period,
        "strategy": strategy,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "direction": direction,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def chart_comparison_rows(
    before: dict[str, str | float] | None,
    after: dict[str, str | float],
) -> list[dict[str, str | float]]:
    if not before:
        return []
    return [
        {"Campo": "Estrategia", "Antes": before["strategy"], "Despues": after["strategy"]},
        {"Campo": "Symbol", "Antes": before["symbol"], "Despues": after["symbol"]},
        {"Campo": "Intervalo", "Antes": before["interval"], "Despues": after["interval"]},
        {"Campo": "Entry", "Antes": before["entry"], "Despues": after["entry"]},
        {"Campo": "SL", "Antes": before["stop_loss"], "Despues": after["stop_loss"]},
        {"Campo": "TP", "Antes": before["take_profit"], "Despues": after["take_profit"]},
    ]


def record_from_chart_levels(
    signal,
    timeframe: str,
    strategy: str,
    entry: float,
    stop_loss: float,
    take_profit: float,
    created_at: datetime | None = None,
) -> RecommendationRecord:
    timestamp = created_at or datetime.now(timezone.utc)
    signal_key = "|".join(
        [
            signal.symbol,
            signal.direction.value,
            timeframe,
            strategy,
            f"{entry:.5f}",
            f"{stop_loss:.5f}",
            f"{take_profit:.5f}",
            timestamp.date().isoformat(),
        ]
    )
    return RecommendationRecord(
        signal_key=signal_key,
        created_at=timestamp,
        symbol=signal.symbol,
        display_symbol=signal.display_symbol,
        direction=signal.direction.value,
        timeframe=timeframe,
        entry=entry,
        stop_loss=stop_loss,
        take_profit=take_profit,
        score=signal.score,
        risk_reward=signal.risk_reward,
        strategy_tags=(strategy,),
        reasons=signal.reasons,
    )


def chart_snapshot_record_from_pair(
    signal_key: str,
    signal,
    timeframe: str,
    strategy: str,
    before_snapshot: dict,
    after_metadata: dict[str, str | float],
    before_figure,
    after_figure,
) -> ChartSnapshotRecord:
    created_at = datetime.now(timezone.utc)
    snapshot_key = "|".join(
        [
            signal_key,
            str(before_snapshot["metadata"]["generated_at"]),
            str(after_metadata["generated_at"]),
        ]
    )
    return ChartSnapshotRecord(
        snapshot_key=snapshot_key,
        signal_key=signal_key,
        created_at=created_at,
        symbol=signal.symbol,
        display_symbol=signal.display_symbol,
        direction=signal.direction.value,
        timeframe=timeframe,
        strategy=strategy,
        before_entry=float(before_snapshot["metadata"]["entry"]),
        before_stop_loss=float(before_snapshot["metadata"]["stop_loss"]),
        before_take_profit=float(before_snapshot["metadata"]["take_profit"]),
        after_entry=float(after_metadata["entry"]),
        after_stop_loss=float(after_metadata["stop_loss"]),
        after_take_profit=float(after_metadata["take_profit"]),
        before_generated_at=str(before_snapshot["metadata"]["generated_at"]),
        after_generated_at=str(after_metadata["generated_at"]),
        before_figure_json=before_figure.to_json(),
        after_figure_json=after_figure.to_json(),
    )


def entry_change_tolerance(entry: float) -> float:
    return max(abs(entry) * 0.0001, 0.00001)


def chart_snapshot_rows(records: list[ChartSnapshotRecord]) -> list[dict[str, str | float]]:
    return [
        {
            "Created": record.created_at.strftime("%Y-%m-%d %H:%M"),
            "Symbol": record.display_symbol,
            "Direction": record.direction,
            "Strategy": record.strategy,
            "Before Entry": record.before_entry,
            "After Entry": record.after_entry,
            "Before SL": record.before_stop_loss,
            "After SL": record.after_stop_loss,
            "Before TP": record.before_take_profit,
            "After TP": record.after_take_profit,
            "Signal Key": record.signal_key,
        }
        for record in records
    ]


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
            "Entry Triggered": record.entry_triggered_at.strftime("%Y-%m-%d %H:%M")
            if record.entry_triggered_at
            else "",
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
            "Feedback": record.feedback,
        }
        for record in records
    ]


def signal_detail_html(signal, supported_profiles: tuple[str, ...]) -> str:
    return f"""
    <div class="signal-panel">
        <div class="panel-topline">
            <span class="badge {signal.direction.value.lower()}">{escape(signal.direction.value)}</span>
            <span>{escape(signal.display_symbol)}</span>
            <span>Score {signal.score}%</span>
            <span>R:R {signal.risk_reward}</span>
        </div>
        <div class="level-grid">
            <div><span>Entrada</span><strong>{signal.entry}</strong></div>
            <div><span>Stop Loss</span><strong class="risk">{signal.stop_loss}</strong></div>
            <div><span>Take Profit</span><strong class="win">{signal.take_profit}</strong></div>
        </div>
        <div class="panel-note">Razones: {escape(", ".join(signal.reasons))}</div>
        <div class="panel-note">Estrategias a favor: {len(supported_profiles)} - {escape(", ".join(supported_profiles))}</div>
    </div>
    """


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #0b0a10; color: #f5f3ff; }
        .block-container { padding-top: 1.1rem; padding-bottom: 2rem; }
        [data-testid="stSidebar"] {
            background: #15111f;
            border-right: 1px solid #312e44;
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.22);
        }
        h1, h2, h3 { color: #fb923c; }
        div[data-testid="stMetricValue"] { color: #fb923c; }
        div[data-testid="stTabs"] {
            background: #0f0d16;
            border: 1px solid #2f293d;
            border-radius: 8px;
            padding: 6px 8px 0 8px;
        }
        div[data-testid="stTabs"] button {
            color: #f5f3ff;
            border-radius: 6px 6px 0 0;
            font-weight: 700;
        }
        div[data-testid="stTabs"] button[aria-selected="true"] {
            color: #fb923c;
            border-bottom: 2px solid #fb923c;
            background: #1b1626;
        }
        .stButton > button {
            border-radius: 6px;
            border: 1px solid #45384f;
            font-weight: 700;
        }
        .stButton > button[kind="primary"] {
            background: #f97316;
            border-color: #f97316;
            color: #111827;
        }
        .command-header {
            display: flex;
            justify-content: space-between;
            gap: 18px;
            align-items: center;
            padding: 18px 20px;
            margin-bottom: 16px;
            border: 1px solid #38304c;
            border-radius: 8px;
            background:
                linear-gradient(135deg, rgba(249, 115, 22, 0.14), rgba(56, 189, 248, 0.08)),
                #100d18;
        }
        .eyebrow {
            color: #38bdf8;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0;
            margin-bottom: 4px;
        }
        .command-title {
            color: #fff7ed;
            font-size: 2.1rem;
            line-height: 1.1;
            font-weight: 900;
        }
        .command-subtitle {
            color: #c7bfd8;
            margin-top: 6px;
        }
        .command-pills {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            justify-content: flex-end;
        }
        .command-pills span {
            background: #1f2937;
            border: 1px solid #38304c;
            color: #f5f3ff;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: 800;
        }
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 10px;
            margin: 12px 0 18px 0;
        }
        .command-metric {
            background: #15111f;
            border: 1px solid #38304c;
            border-left: 4px solid #fb923c;
            border-radius: 7px;
            padding: 12px 14px;
            min-height: 86px;
        }
        .command-metric.green { border-left-color: #22c55e; }
        .command-metric.red { border-left-color: #ef4444; }
        .command-metric.cyan { border-left-color: #38bdf8; }
        .metric-label {
            color: #a9a0b8;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .metric-value {
            color: #fff7ed;
            font-size: 1.65rem;
            font-weight: 900;
            margin-top: 5px;
        }
        .metric-detail {
            color: #c7bfd8;
            font-size: 0.82rem;
            margin-top: 4px;
        }
        .section-heading {
            margin: 20px 0 10px 0;
        }
        .section-heading h2 {
            margin: 0;
            color: #fff7ed;
        }
        .section-subtitle {
            color: #a9a0b8;
            margin-top: 4px;
        }
        .signal-panel {
            background: #15111f;
            border: 1px solid #38304c;
            border-radius: 8px;
            padding: 14px 16px;
            margin: 10px 0 18px 0;
        }
        .panel-topline {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            color: #f5f3ff;
            font-weight: 800;
        }
        .badge {
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 900;
        }
        .badge.long { background: rgba(34, 197, 94, 0.18); color: #86efac; border: 1px solid #22c55e; }
        .badge.short { background: rgba(239, 68, 68, 0.18); color: #fca5a5; border: 1px solid #ef4444; }
        .level-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 10px;
            margin-top: 12px;
        }
        .level-grid div {
            background: #0f0d16;
            border: 1px solid #2f293d;
            border-radius: 6px;
            padding: 10px;
        }
        .level-grid span {
            display: block;
            color: #a9a0b8;
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
        }
        .level-grid strong {
            color: #fff7ed;
            display: block;
            margin-top: 3px;
            font-size: 1.08rem;
        }
        .level-grid .risk { color: #fca5a5; }
        .level-grid .win { color: #86efac; }
        .panel-note {
            color: #c7bfd8;
            margin-top: 10px;
        }
        .disclaimer {
            color: #d8d5e8;
            background: #1b1626;
            border-left: 4px solid #f97316;
            padding: 10px 12px;
            border-radius: 6px;
        }
        @media (max-width: 900px) {
            .command-header { align-items: flex-start; flex-direction: column; }
            .metric-grid, .level-grid { grid-template-columns: 1fr; }
            .command-title { font-size: 1.6rem; }
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
    st.markdown(command_center_header_html(), unsafe_allow_html=True)
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
    st.markdown(
        '<div class="metric-grid">'
        + command_metric_card("Senales", len(signals), "green", "Oportunidades filtradas")
        + command_metric_card("Score minimo", f"{min_score}%", "orange", "Umbral de calidad")
        + command_metric_card("Riesgo", "1%", "red", "Por operacion")
        + command_metric_card("Mercados", len(selected_symbols), "cyan", "Simbolos activos")
        + "</div>",
        unsafe_allow_html=True,
    )

    store = JournalStore()
    if auto_record:
        inserted = 0
        for signal in signals:
            if store.insert_recommendation(record_from_signal(signal)):
                inserted += 1
        if inserted:
            st.toast(f"Recomendaciones registradas: {inserted}")

    scanner_tab, journal_tab, feedback_tab = st.tabs(["Buscar", "Registro", "Feedback"])

    with scanner_tab:
        st.markdown(
            section_header_html("Oportunidades", "Ranking de setups detectados con las reglas actuales."),
            unsafe_allow_html=True,
        )
        if signals:
            st.dataframe(signals_to_frame(signals), use_container_width=True, hide_index=True)
            selected = st.selectbox("Detalle de senal", [signal.display_symbol for signal in signals])
            signal = next(item for item in signals if item.display_symbol == selected)
            supported_profiles = classify_strategy_profiles(signal)
            st.markdown(signal_detail_html(signal, supported_profiles), unsafe_allow_html=True)

            st.markdown(
                section_header_html("Grafico y niveles de trade", "Zoom con rueda del mouse y niveles por estrategia."),
                unsafe_allow_html=True,
            )
            show_chart_comparison = st.toggle("Mostrar comparacion antes/despues", value=True)
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
                current_snapshot_metadata = chart_snapshot_metadata(
                    symbol=signal.display_symbol,
                    interval=chart_interval,
                    period=chart_period,
                    strategy=strategy_chart_choice,
                    entry=levels.entry,
                    stop_loss=levels.stop_loss,
                    take_profit=levels.take_profit,
                    direction=signal.direction.value,
                )
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
                snapshots_by_key = st.session_state.setdefault("chart_snapshots_by_key", {})
                current_snapshot_key = chart_snapshot_key(current_snapshot_metadata)
                previous_snapshot = snapshots_by_key.get(current_snapshot_key)
                can_compare = show_chart_comparison and same_snapshot_context(
                    previous_snapshot["metadata"] if previous_snapshot else None,
                    current_snapshot_metadata,
                )
                if can_compare:
                    st.dataframe(
                        chart_comparison_rows(previous_snapshot["metadata"], current_snapshot_metadata),
                        use_container_width=True,
                        hide_index=True,
                    )
                    before_col, after_col = st.columns(2)
                    with before_col:
                        st.markdown(
                            section_header_html(
                                "Antes",
                                f'{previous_snapshot["metadata"]["strategy"]} | {previous_snapshot["metadata"]["generated_at"]}',
                            ),
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(
                            previous_snapshot["figure"],
                            use_container_width=True,
                            config=plotly_chart_config(),
                            key="before_chart_snapshot",
                        )
                    with after_col:
                        st.markdown(
                            section_header_html(
                                "Despues",
                                f'{current_snapshot_metadata["strategy"]} | {current_snapshot_metadata["generated_at"]}',
                            ),
                            unsafe_allow_html=True,
                        )
                        st.plotly_chart(
                            fig,
                            use_container_width=True,
                            config=plotly_chart_config(),
                            key="after_chart_snapshot",
                        )

                    if entry_changed(
                        previous_snapshot["metadata"],
                        current_snapshot_metadata,
                        tolerance=entry_change_tolerance(levels.entry),
                    ):
                        chart_record = record_from_chart_levels(
                            signal=signal,
                            timeframe=chart_interval,
                            strategy=strategy_chart_choice,
                            entry=levels.entry,
                            stop_loss=levels.stop_loss,
                            take_profit=levels.take_profit,
                        )
                        inserted_signal = store.insert_recommendation(chart_record)
                        inserted_snapshot = store.insert_chart_snapshot(
                            chart_snapshot_record_from_pair(
                                signal_key=chart_record.signal_key,
                                signal=signal,
                                timeframe=chart_interval,
                                strategy=strategy_chart_choice,
                                before_snapshot=previous_snapshot,
                                after_metadata=current_snapshot_metadata,
                                before_figure=previous_snapshot["figure"],
                                after_figure=fig,
                            )
                        )
                        if inserted_signal or inserted_snapshot:
                            st.toast("Nueva entrada registrada con evolucion grafica.")
                else:
                    st.plotly_chart(fig, use_container_width=True, config=plotly_chart_config())

                snapshots_by_key[current_snapshot_key] = {
                    "metadata": current_snapshot_metadata,
                    "figure": fig,
                }
                st.session_state["chart_snapshots_by_key"] = snapshots_by_key

                supported = [item for item in evaluations if item.profile in supported_profiles and item.setups > 0]
                combined_win_rate = sum(item.win_rate for item in supported) / len(supported) if supported else 0.0
                combined_setups = sum(item.setups for item in supported)
                st.markdown(
                    section_header_html("Evaluacion historica de estrategias", "Win rate y riesgo por perfil de setup."),
                    unsafe_allow_html=True,
                )
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
        st.markdown(
            section_header_html("Registro autonomo", "Ciclo completo: recomendacion, entrada activada, TP/SL y resultado."),
            unsafe_allow_html=True,
        )
        st.caption(
            "Este registro mide resultados historicos de recomendaciones guardadas. "
            "En Streamlit Cloud, el registro local puede reiniciarse; para persistencia real conecta Supabase/Postgres."
        )
        if st.button("Actualizar recomendaciones abiertas"):
            updated_count = 0
            for record in store.list_recommendations():
                if record.status not in {JournalStatus.WAITING_ENTRY, JournalStatus.OPEN}:
                    continue
                try:
                    history = load_history(record.symbol, period="730d", interval=record.timeframe)
                    updated = resolve_recommendation(record, history)
                    if (
                        updated.status != record.status
                        or updated.outcome_r != record.outcome_r
                        or updated.entry_triggered_at != record.entry_triggered_at
                        or updated.feedback != record.feedback
                    ):
                        store.update_resolution(
                            record.signal_key,
                            updated.status,
                            updated.outcome_r,
                            updated.resolution_note,
                            updated.resolved_at,
                            entry_triggered_at=updated.entry_triggered_at,
                            feedback=updated.feedback,
                        )
                        updated_count += 1
                except Exception as exc:
                    st.warning(f"No se pudo evaluar {record.display_symbol}: {exc}")
            st.success(f"Recomendaciones actualizadas: {updated_count}")

        records = store.list_recommendations()
        summary = journal_summary(records)
        st.markdown(
            '<div class="metric-grid">'
            + command_metric_card("Total", summary["total"], "cyan")
            + command_metric_card("TP", summary["wins"], "green")
            + command_metric_card("SL", summary["losses"], "red")
            + command_metric_card("Esperando entrada", summary["waiting_entry"], "orange")
            + command_metric_card("% acierto", f'{summary["hit_rate"]:.1f}%', "green")
            + command_metric_card("% activacion", f'{summary["activation_rate"]:.1f}%', "cyan")
            + command_metric_card("Abiertas", summary["open"], "orange")
            + command_metric_card("Average R", summary["average_r"], "cyan")
            + "</div>",
            unsafe_allow_html=True,
        )

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

            chart_snapshots = store.list_chart_snapshots()
            if chart_snapshots:
                st.subheader("Evolucion grafica guardada")
                st.dataframe(chart_snapshot_rows(chart_snapshots), use_container_width=True, hide_index=True)
                selected_snapshot = st.selectbox(
                    "Ver evolucion grafica",
                    [snapshot.snapshot_key for snapshot in chart_snapshots],
                    format_func=lambda key: next(
                        (
                            f"{snapshot.display_symbol} | {snapshot.strategy} | "
                            f"{snapshot.before_generated_at} -> {snapshot.after_generated_at}"
                            for snapshot in chart_snapshots
                            if snapshot.snapshot_key == key
                        ),
                        key,
                    ),
                )
                snapshot = next(item for item in chart_snapshots if item.snapshot_key == selected_snapshot)
                before_col, after_col = st.columns(2)
                with before_col:
                    st.markdown(section_header_html("Antes guardado", snapshot.before_generated_at), unsafe_allow_html=True)
                    st.plotly_chart(
                        pio.from_json(snapshot.before_figure_json),
                        use_container_width=True,
                        config=plotly_chart_config(),
                        key=f"stored_before_{snapshot.snapshot_key}",
                    )
                with after_col:
                    st.markdown(section_header_html("Despues guardado", snapshot.after_generated_at), unsafe_allow_html=True)
                    st.plotly_chart(
                        pio.from_json(snapshot.after_figure_json),
                        use_container_width=True,
                        config=plotly_chart_config(),
                        key=f"stored_after_{snapshot.snapshot_key}",
                    )
        else:
            st.info("Aun no hay recomendaciones registradas.")

    with feedback_tab:
        st.markdown(
            section_header_html("Feedback de estrategias", "Lectura historica para mejorar reglas y priorizar setups."),
            unsafe_allow_html=True,
        )
        records = store.list_recommendations()
        if records:
            feedback_rows = strategy_feedback_rows(records)
            st.dataframe(feedback_rows, use_container_width=True, hide_index=True)
            resolved = [row for row in feedback_rows if row["wins"] + row["losses"] > 0]
            if resolved:
                best = max(resolved, key=lambda row: (row["hit_rate"], row["average_r"]))
                weakest = min(resolved, key=lambda row: (row["hit_rate"], row["average_r"]))
                c1, c2 = st.columns(2)
                c1.metric("Mejor estrategia", best["strategy"], f'{best["hit_rate"]:.1f}% acierto')
                c2.metric("Estrategia a revisar", weakest["strategy"], f'{weakest["hit_rate"]:.1f}% acierto')
            st.caption(
                "El feedback es deterministico y educativo: resume resultados historicos, no garantiza ganancias futuras."
            )
        else:
            st.info("Aun no hay feedback. Guarda recomendaciones y actualizalas para empezar a medir.")

    if errors:
        with st.expander("Errores de datos"):
            for error in errors:
                st.warning(error)


if __name__ == "__main__":
    main()
