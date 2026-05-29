from dataclasses import dataclass

import pandas as pd


REQUIRED_OHLCV_COLUMNS = ("open", "high", "low", "close", "volume")


@dataclass(frozen=True)
class MarketSymbol:
    display: str
    provider_symbol: str
    market: str


def validate_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    normalized.columns = [str(column).strip().lower() for column in normalized.columns]
    missing = [column for column in REQUIRED_OHLCV_COLUMNS if column not in normalized.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(missing)}")

    result = normalized.loc[:, REQUIRED_OHLCV_COLUMNS].copy()
    for column in REQUIRED_OHLCV_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    return result.dropna(subset=["open", "high", "low", "close"])
