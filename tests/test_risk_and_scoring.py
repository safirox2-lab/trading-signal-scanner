from src.models.signals import Direction
from src.risk.position_sizing import position_size
from src.risk.trade_plan import build_trade_plan, score_signal


def test_position_size_risks_one_percent():
    result = position_size(account_balance=10_000, risk_percent=1, entry=100, stop_loss=95)

    assert result.amount_at_risk == 100
    assert result.units == 20


def test_build_trade_plan_long_uses_two_r_target():
    plan = build_trade_plan(Direction.LONG, account_balance=10_000, entry=100, stop_loss=95)

    assert plan.take_profit == 110
    assert plan.risk_reward == 2


def test_build_trade_plan_short_uses_two_r_target():
    plan = build_trade_plan(Direction.SHORT, account_balance=10_000, entry=100, stop_loss=105)

    assert plan.take_profit == 90
    assert plan.risk_reward == 2


def test_score_signal_caps_at_one_hundred():
    score, reasons = score_signal(
        trend_aligned=True,
        valid_order_block=True,
        structure_break=True,
        fvg=True,
        liquidity_sweep=True,
        ema_momentum=True,
        risk_reward_ok=True,
        atr_rsi_quality=True,
    )

    assert score == 100
    assert "trend aligned" in reasons
