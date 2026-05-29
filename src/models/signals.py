from dataclasses import dataclass
from enum import Enum


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


@dataclass(frozen=True)
class TradePlan:
    entry: float
    stop_loss: float
    take_profit: float
    risk_reward: float
    position_size: float
    amount_at_risk: float


@dataclass(frozen=True)
class SignalCandidate:
    symbol: str
    display_symbol: str
    direction: Direction
    timeframe: str
    entry: float
    stop_loss: float
    take_profit: float
    score: int
    risk_reward: float
    strategy_tags: tuple[str, ...]
    reasons: tuple[str, ...]
