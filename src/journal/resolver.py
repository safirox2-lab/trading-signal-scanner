from dataclasses import replace
from datetime import datetime, timezone

import pandas as pd

from src.journal.feedback import outcome_feedback
from src.journal.models import JournalStatus, RecommendationRecord


def resolve_recommendation(record: RecommendationRecord, history: pd.DataFrame) -> RecommendationRecord:
    if record.status not in {JournalStatus.WAITING_ENTRY, JournalStatus.OPEN}:
        return record

    active_record = record
    entry_seen = record.status == JournalStatus.OPEN
    for timestamp, candle in _eligible_history(record, history).iterrows():
        high = float(candle["high"])
        low = float(candle["low"])
        event_at = _event_time(timestamp)
        if not entry_seen:
            if not _entry_hit(active_record, high, low):
                continue
            entry_seen = True
            active_record = replace(
                active_record,
                status=JournalStatus.OPEN,
                entry_triggered_at=event_at,
                feedback=outcome_feedback(active_record, JournalStatus.OPEN),
            )

        if active_record.direction == "LONG":
            stop_hit = low <= active_record.stop_loss
            target_hit = high >= active_record.take_profit
        else:
            stop_hit = high >= active_record.stop_loss
            target_hit = low <= active_record.take_profit
        if stop_hit:
            return replace(
                active_record,
                status=JournalStatus.SL,
                outcome_r=-1.0,
                resolved_at=event_at,
                resolution_note="SL touched before TP or same candle as TP",
                feedback=outcome_feedback(active_record, JournalStatus.SL),
            )
        if target_hit:
            return replace(
                active_record,
                status=JournalStatus.TP,
                outcome_r=active_record.risk_reward,
                resolved_at=event_at,
                resolution_note="TP touched before SL",
                feedback=outcome_feedback(active_record, JournalStatus.TP),
            )
    if entry_seen:
        return active_record
    return replace(record, feedback=outcome_feedback(record, JournalStatus.WAITING_ENTRY))


def _entry_hit(record: RecommendationRecord, high: float, low: float) -> bool:
    return low <= record.entry <= high


def _eligible_history(record: RecommendationRecord, history: pd.DataFrame) -> pd.DataFrame:
    if isinstance(history.index, pd.DatetimeIndex):
        created_at = record.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        index = history.index
        if index.tz is None:
            created_at = created_at.replace(tzinfo=None)
        return history[index >= created_at]
    return history


def _event_time(timestamp) -> datetime:
    if isinstance(timestamp, pd.Timestamp):
        value = timestamp.to_pydatetime()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return datetime.now(timezone.utc)
