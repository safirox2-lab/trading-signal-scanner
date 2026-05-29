from collections import defaultdict

from src.journal.models import JournalStatus, RecommendationRecord


def _hit_rate(wins: int, losses: int) -> float:
    resolved = wins + losses
    return round((wins / resolved) * 100, 2) if resolved else 0.0


def journal_summary(records: list[RecommendationRecord]) -> dict[str, float | int]:
    wins = len([record for record in records if record.status == JournalStatus.TP])
    losses = len([record for record in records if record.status == JournalStatus.SL])
    open_count = len([record for record in records if record.status == JournalStatus.OPEN])
    resolved_r = [record.outcome_r for record in records if record.outcome_r is not None]
    return {
        "total": len(records),
        "wins": wins,
        "losses": losses,
        "open": open_count,
        "hit_rate": _hit_rate(wins, losses),
        "average_r": round(sum(resolved_r) / len(resolved_r), 2) if resolved_r else 0.0,
    }


def hit_rate_by_strategy(records: list[RecommendationRecord]) -> list[dict[str, float | int | str]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0})
    for record in records:
        if record.status not in {JournalStatus.TP, JournalStatus.SL}:
            continue
        for tag in record.strategy_tags:
            if record.status == JournalStatus.TP:
                buckets[tag]["wins"] += 1
            else:
                buckets[tag]["losses"] += 1
    return [
        {
            "strategy": strategy,
            "wins": values["wins"],
            "losses": values["losses"],
            "hit_rate": _hit_rate(values["wins"], values["losses"]),
        }
        for strategy, values in sorted(buckets.items())
    ]


def hit_rate_by_symbol(records: list[RecommendationRecord]) -> list[dict[str, float | int | str]]:
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: {"wins": 0, "losses": 0})
    for record in records:
        if record.status not in {JournalStatus.TP, JournalStatus.SL}:
            continue
        if record.status == JournalStatus.TP:
            buckets[record.symbol]["wins"] += 1
        else:
            buckets[record.symbol]["losses"] += 1
    return [
        {
            "symbol": symbol,
            "wins": values["wins"],
            "losses": values["losses"],
            "hit_rate": _hit_rate(values["wins"], values["losses"]),
        }
        for symbol, values in sorted(buckets.items())
    ]
