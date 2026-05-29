from src.evaluation.strategy_profiles import classify_strategy_profiles, confluence_summary
from src.models.signals import Direction, SignalCandidate


def make_signal(reasons: tuple[str, ...], tags: tuple[str, ...] = ("EMA MOMENTUM",)) -> SignalCandidate:
    return SignalCandidate(
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction=Direction.LONG,
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=tags,
        reasons=reasons,
    )


def test_classify_strategy_profiles_maps_reasons_to_profiles():
    signal = make_signal(("trend aligned", "valid order block", "fair value gap", "liquidity sweep", "EMA momentum"))

    profiles = classify_strategy_profiles(signal)

    assert "Trend Alignment" in profiles
    assert "Order Block" in profiles
    assert "FVG / Imbalance" in profiles
    assert "Liquidity Sweep" in profiles
    assert "Scalping / EMA Momentum" in profiles


def test_confluence_summary_counts_profiles():
    signal = make_signal(("trend aligned", "valid order block", "EMA momentum"))

    summary = confluence_summary(signal, historical_win_rate=61.8, historical_setups=112)

    assert "3 strategies support this LONG setup" in summary
    assert "61.8%" in summary
    assert "112 setups" in summary
