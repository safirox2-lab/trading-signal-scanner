from src.indicators.imbalance import fair_value_gaps
from src.indicators.momentum import ema_cross_direction, rsi
from src.indicators.trend import ema, trend_regime
from src.indicators.volatility import atr
from src.models.market import validate_ohlcv
from src.models.signals import Direction, SignalCandidate
from src.risk.trade_plan import build_trade_plan, score_signal
from src.strategies.liquidity import liquidity_sweep
from src.strategies.order_blocks import order_block_candidates


def scan_symbol(
    provider,
    display_symbol: str,
    provider_symbol: str,
    timeframe: str,
    account_balance: float,
    min_score: int = 70,
    period: str = "6mo",
) -> SignalCandidate | None:
    df = validate_ohlcv(provider.history(provider_symbol, period=period, interval=timeframe))
    if len(df) < 60:
        return None
    regime = trend_regime(df, fast_span=20, slow_span=50)
    close = df["close"]
    fast = ema(close, 9)
    slow = ema(close, 21)
    cross = ema_cross_direction(fast, slow)
    blocks = order_block_candidates(df)
    latest_block = blocks[-1] if blocks else None
    gaps = fair_value_gaps(df)
    latest_gap = gaps.iloc[-1]
    sweep = liquidity_sweep(df)
    latest_atr = float(atr(df).iloc[-1])
    latest_rsi = float(rsi(close).iloc[-1])

    direction = Direction.LONG if regime == "bullish" else Direction.SHORT if regime == "bearish" else Direction.LONG
    if latest_block and latest_block["direction"] == "short":
        direction = Direction.SHORT

    entry = float(close.iloc[-1])
    if direction == Direction.LONG:
        stop_loss = min(entry - latest_atr, float(latest_block["low"]) if latest_block else entry - latest_atr)
    else:
        stop_loss = max(entry + latest_atr, float(latest_block["high"]) if latest_block else entry + latest_atr)
    plan = build_trade_plan(direction, account_balance, entry, stop_loss)

    trend_aligned = (direction == Direction.LONG and regime == "bullish") or (
        direction == Direction.SHORT and regime == "bearish"
    )
    score, reasons = score_signal(
        trend_aligned=trend_aligned,
        valid_order_block=latest_block is not None,
        structure_break=True,
        fvg=latest_gap["type"] is not None,
        liquidity_sweep=sweep is not None,
        ema_momentum=(cross == "long" and direction == Direction.LONG) or (cross == "short" and direction == Direction.SHORT),
        risk_reward_ok=plan.risk_reward >= 2,
        atr_rsi_quality=latest_atr > 0 and 20 < latest_rsi < 80,
    )
    if score < min_score:
        return None
    tags = tuple(reason.upper() for reason in reasons[:4])
    return SignalCandidate(
        symbol=provider_symbol,
        display_symbol=display_symbol,
        direction=direction,
        timeframe=timeframe,
        entry=round(plan.entry, 5),
        stop_loss=round(plan.stop_loss, 5),
        take_profit=round(plan.take_profit, 5),
        score=score,
        risk_reward=plan.risk_reward,
        strategy_tags=tags,
        reasons=reasons,
    )
