from dataclasses import replace
from datetime import datetime, timezone

import pandas as pd

from src.journal.models import JournalStatus, RecommendationRecord


def resolve_recommendation(record: RecommendationRecord, history: pd.DataFrame) -> RecommendationRecord:
    if record.status != JournalStatus.OPEN:
        return record
    for _, candle in history.iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        if record.direction == "LONG":
            stop_hit = low <= record.stop_loss
            target_hit = high >= record.take_profit
        else:
            stop_hit = high >= record.stop_loss
            target_hit = low <= record.take_profit
        if stop_hit:
            return replace(
                record,
                status=JournalStatus.SL,
                outcome_r=-1.0,
                resolved_at=datetime.now(timezone.utc),
                resolution_note="SL touched before TP or same candle as TP",
            )
        if target_hit:
            return replace(
                record,
                status=JournalStatus.TP,
                outcome_r=record.risk_reward,
                resolved_at=datetime.now(timezone.utc),
                resolution_note="TP touched before SL",
            )
    return record
