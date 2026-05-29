from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from src.models.signals import SignalCandidate


class JournalStatus(str, Enum):
    WAITING_ENTRY = "WAITING_ENTRY"
    OPEN = "OPEN"
    TP = "TP"
    SL = "SL"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class RecommendationRecord:
    signal_key: str
    created_at: datetime
    symbol: str
    display_symbol: str
    direction: str
    timeframe: str
    entry: float
    stop_loss: float
    take_profit: float
    score: int
    risk_reward: float
    strategy_tags: tuple[str, ...]
    reasons: tuple[str, ...]
    status: JournalStatus = JournalStatus.WAITING_ENTRY
    entry_triggered_at: datetime | None = None
    outcome_r: float | None = None
    resolved_at: datetime | None = None
    resolution_note: str = ""
    feedback: str = ""


def stable_signal_key(signal: SignalCandidate, created_at: datetime | None = None) -> str:
    timestamp = created_at or datetime.now(timezone.utc)
    signal_date = timestamp.date().isoformat()
    return "|".join(
        [
            signal.symbol,
            signal.direction.value,
            signal.timeframe,
            f"{signal.entry:.5f}",
            f"{signal.stop_loss:.5f}",
            f"{signal.take_profit:.5f}",
            signal_date,
        ]
    )


def record_from_signal(signal: SignalCandidate, created_at: datetime | None = None) -> RecommendationRecord:
    timestamp = created_at or datetime.now(timezone.utc)
    return RecommendationRecord(
        signal_key=stable_signal_key(signal, timestamp),
        created_at=timestamp,
        symbol=signal.symbol,
        display_symbol=signal.display_symbol,
        direction=signal.direction.value,
        timeframe=signal.timeframe,
        entry=signal.entry,
        stop_loss=signal.stop_loss,
        take_profit=signal.take_profit,
        score=signal.score,
        risk_reward=signal.risk_reward,
        strategy_tags=signal.strategy_tags,
        reasons=signal.reasons,
    )
