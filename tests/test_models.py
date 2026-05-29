import pandas as pd
import pytest

from src.models.market import MarketSymbol, validate_ohlcv
from src.models.signals import Direction, SignalCandidate


def test_validate_ohlcv_accepts_required_columns():
    df = pd.DataFrame(
        {
            "open": [1.0],
            "high": [1.2],
            "low": [0.9],
            "close": [1.1],
            "volume": [100],
        }
    )

    validated = validate_ohlcv(df)

    assert list(validated.columns) == ["open", "high", "low", "close", "volume"]


def test_validate_ohlcv_rejects_missing_columns():
    with pytest.raises(ValueError, match="Missing OHLCV columns"):
        validate_ohlcv(pd.DataFrame({"close": [1.0]}))


def test_signal_candidate_uses_direction_enum():
    signal = SignalCandidate(
        symbol="EURUSD=X",
        display_symbol="EUR/USD",
        direction=Direction.LONG,
        timeframe="1h",
        entry=1.1,
        stop_loss=1.09,
        take_profit=1.12,
        score=80,
        risk_reward=2.0,
        strategy_tags=("EMA", "OB"),
        reasons=("trend aligned",),
    )

    assert signal.direction.value == "LONG"
    assert signal.score == 80


def test_market_symbol_stores_provider_symbol():
    symbol = MarketSymbol(display="EUR/USD", provider_symbol="EURUSD=X", market="forex")

    assert symbol.provider_symbol == "EURUSD=X"
