import pandas as pd
import yfinance as yf

from src.models.market import validate_ohlcv


class YFinanceProvider:
    def history(self, symbol: str, period: str = "6mo", interval: str = "1h") -> pd.DataFrame:
        df = yf.download(symbol, period=period, interval=interval, progress=False, auto_adjust=False)
        if df.empty:
            raise ValueError(f"No market data returned for {symbol}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [column[0] for column in df.columns]
        renamed = df.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
            }
        )
        return validate_ohlcv(renamed)
