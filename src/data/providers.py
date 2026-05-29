from typing import Protocol

import pandas as pd

from src.models.market import MarketSymbol


class MarketDataProvider(Protocol):
    def history(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        raise NotImplementedError


def default_symbols() -> tuple[MarketSymbol, ...]:
    return (
        MarketSymbol("EUR/USD", "EURUSD=X", "forex"),
        MarketSymbol("GBP/USD", "GBPUSD=X", "forex"),
        MarketSymbol("USD/JPY", "JPY=X", "forex"),
        MarketSymbol("AUD/USD", "AUDUSD=X", "forex"),
        MarketSymbol("USD/CAD", "CAD=X", "forex"),
        MarketSymbol("S&P 500", "^GSPC", "indices"),
        MarketSymbol("NASDAQ 100", "^NDX", "indices"),
        MarketSymbol("Dow Jones", "^DJI", "indices"),
        MarketSymbol("Gold", "GC=F", "commodities"),
    )
