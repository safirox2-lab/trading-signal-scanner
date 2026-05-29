from dataclasses import dataclass


@dataclass(frozen=True)
class PositionSize:
    units: float
    amount_at_risk: float
    stop_distance: float


def position_size(account_balance: float, risk_percent: float, entry: float, stop_loss: float) -> PositionSize:
    if account_balance <= 0:
        raise ValueError("Account balance must be positive")
    if risk_percent <= 0:
        raise ValueError("Risk percent must be positive")
    stop_distance = abs(float(entry) - float(stop_loss))
    if stop_distance <= 0:
        raise ValueError("Stop distance must be positive")
    amount_at_risk = float(account_balance) * (float(risk_percent) / 100)
    return PositionSize(units=amount_at_risk / stop_distance, amount_at_risk=amount_at_risk, stop_distance=stop_distance)
