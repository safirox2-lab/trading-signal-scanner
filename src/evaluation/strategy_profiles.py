from src.models.signals import SignalCandidate


PROFILE_REASON_MAP = {
    "Trend Alignment": ("trend aligned",),
    "Order Block": ("valid order block", "order block"),
    "FVG / Imbalance": ("fair value gap", "fvg"),
    "Liquidity Sweep": ("liquidity sweep",),
    "Scalping / EMA Momentum": ("ema momentum", "ema"),
}


def classify_strategy_profiles(signal: SignalCandidate) -> tuple[str, ...]:
    haystack = " ".join(signal.reasons + signal.strategy_tags).lower()
    profiles = []
    for profile, needles in PROFILE_REASON_MAP.items():
        if any(needle in haystack for needle in needles):
            profiles.append(profile)
    return tuple(profiles)


def confluence_summary(signal: SignalCandidate, historical_win_rate: float, historical_setups: int) -> str:
    profiles = classify_strategy_profiles(signal)
    return (
        f"{len(profiles)} strategies support this {signal.direction.value} setup. "
        f"Historically, similar setups reached TP first {historical_win_rate:.1f}% "
        f"of the time over {historical_setups} setups."
    )
