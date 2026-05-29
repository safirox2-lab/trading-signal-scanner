from collections import defaultdict

from src.journal.models import JournalStatus, RecommendationRecord


def _hit_rate(wins: int, losses: int) -> float:
    resolved = wins + losses
    return round((wins / resolved) * 100, 2) if resolved else 0.0


def journal_summary(records: list[RecommendationRecord]) -> dict[str, float | int]:
    wins = len([record for record in records if record.status == JournalStatus.TP])
    losses = len([record for record in records if record.status == JournalStatus.SL])
    open_count = len([record for record in records if record.status == JournalStatus.OPEN])
    waiting_entry = len([record for record in records if record.status == JournalStatus.WAITING_ENTRY])
    activated = len(
        [
            record
            for record in records
            if record.entry_triggered_at is not None or record.status in {JournalStatus.OPEN, JournalStatus.TP, JournalStatus.SL}
        ]
    )
    resolved_r = [record.outcome_r for record in records if record.outcome_r is not None]
    return {
        "total": len(records),
        "wins": wins,
        "losses": losses,
        "open": open_count,
        "waiting_entry": waiting_entry,
        "hit_rate": _hit_rate(wins, losses),
        "activation_rate": round((activated / len(records)) * 100, 2) if records else 0.0,
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


def strategy_feedback_rows(records: list[RecommendationRecord]) -> list[dict[str, float | int | str]]:
    buckets: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"total": 0, "activated": 0, "wins": 0, "losses": 0, "waiting_entry": 0, "r_sum": 0.0, "r_count": 0}
    )
    for record in records:
        for tag in record.strategy_tags:
            bucket = buckets[tag]
            bucket["total"] += 1
            if record.entry_triggered_at is not None or record.status in {JournalStatus.OPEN, JournalStatus.TP, JournalStatus.SL}:
                bucket["activated"] += 1
            if record.status == JournalStatus.WAITING_ENTRY:
                bucket["waiting_entry"] += 1
            if record.status == JournalStatus.TP:
                bucket["wins"] += 1
            if record.status == JournalStatus.SL:
                bucket["losses"] += 1
            if record.outcome_r is not None:
                bucket["r_sum"] += record.outcome_r
                bucket["r_count"] += 1

    rows = []
    for strategy, values in sorted(buckets.items()):
        total = int(values["total"])
        wins = int(values["wins"])
        losses = int(values["losses"])
        waiting_entry = int(values["waiting_entry"])
        activated = int(values["activated"])
        r_count = int(values["r_count"])
        hit_rate = _hit_rate(wins, losses)
        average_r = round(float(values["r_sum"]) / r_count, 2) if r_count else 0.0
        rows.append(
            {
                "strategy": strategy,
                "total": total,
                "wins": wins,
                "losses": losses,
                "waiting_entry": waiting_entry,
                "hit_rate": hit_rate,
                "activation_rate": round((activated / total) * 100, 2) if total else 0.0,
                "average_r": average_r,
                "feedback": _strategy_feedback(hit_rate, average_r, wins, losses, waiting_entry),
            }
        )
    return rows


def _strategy_feedback(hit_rate: float, average_r: float, wins: int, losses: int, waiting_entry: int) -> str:
    if wins + losses >= 3 and hit_rate >= 60 and average_r > 0:
        return "Priorizar en revision: buena tasa de acierto y R positivo."
    if losses >= wins and losses > 0:
        return "Revisar confluencia, confirmacion y distancia de SL antes de aumentar peso."
    if waiting_entry > 0:
        return "Revisar distancia de entrada: varias senales no se activaron."
    return "Aun hacen falta mas muestras para una conclusion fuerte."
