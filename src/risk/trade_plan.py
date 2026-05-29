from src.models.signals import Direction, TradePlan
from src.risk.position_sizing import position_size


def build_trade_plan(
    direction: Direction,
    account_balance: float,
    entry: float,
    stop_loss: float,
    risk_percent: float = 1.0,
    reward_multiple: float = 2.0,
) -> TradePlan:
    size = position_size(account_balance, risk_percent, entry, stop_loss)
    risk_distance = abs(entry - stop_loss)
    if direction == Direction.LONG:
        take_profit = entry + (risk_distance * reward_multiple)
    else:
        take_profit = entry - (risk_distance * reward_multiple)
    return TradePlan(
        entry=float(entry),
        stop_loss=float(stop_loss),
        take_profit=float(take_profit),
        risk_reward=float(reward_multiple),
        position_size=float(size.units),
        amount_at_risk=float(size.amount_at_risk),
    )


def score_signal(
    *,
    trend_aligned: bool,
    valid_order_block: bool,
    structure_break: bool,
    fvg: bool,
    liquidity_sweep: bool,
    ema_momentum: bool,
    risk_reward_ok: bool,
    atr_rsi_quality: bool,
) -> tuple[int, tuple[str, ...]]:
    weights = (
        (trend_aligned, 20, "trend aligned"),
        (valid_order_block, 20, "valid order block"),
        (structure_break, 15, "structure break"),
        (fvg, 10, "fair value gap"),
        (liquidity_sweep, 10, "liquidity sweep"),
        (ema_momentum, 10, "EMA momentum"),
        (risk_reward_ok, 10, "risk/reward >= 1:2"),
        (atr_rsi_quality, 5, "ATR/RSI quality"),
    )
    score = sum(points for enabled, points, _reason in weights if enabled)
    reasons = tuple(reason for enabled, _points, reason in weights if enabled)
    return min(100, score), reasons
