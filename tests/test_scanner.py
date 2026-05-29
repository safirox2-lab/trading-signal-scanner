import pandas as pd

from src.data.providers import MarketDataProvider, default_symbols
from src.strategies.scanner import scan_symbol


class StaticProvider(MarketDataProvider):
    def history(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        rows = []
        price = 100.0
        for index in range(260):
            open_price = price
            close_price = price + 0.2
            rows.append(
                {
                    "open": open_price,
                    "high": close_price + 0.5,
                    "low": open_price - 0.5,
                    "close": close_price,
                    "volume": 1000 + index,
                }
            )
            price = close_price
        return pd.DataFrame(rows)


def test_default_symbols_include_liquid_markets():
    symbols = default_symbols()

    assert any(symbol.display == "EUR/USD" for symbol in symbols)
    assert any(symbol.market == "indices" for symbol in symbols)


def test_scan_symbol_returns_signal_with_risk_fields():
    signal = scan_symbol(
        provider=StaticProvider(),
        display_symbol="TEST",
        provider_symbol="TEST",
        timeframe="1h",
        account_balance=10_000,
        min_score=0,
    )

    assert signal is not None
    assert signal.stop_loss != signal.entry
    assert signal.take_profit != signal.entry
