# Trading Signal Scanner

Local Streamlit app for scanning liquid forex pairs, US index proxies, and gold proxies for technical long/short opportunities.

This is an educational analysis tool. It does not guarantee profit, does not provide financial advice, and does not execute trades.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Data Limitations

The first version uses yfinance for convenient market data access. Data can be delayed, incomplete, or unavailable for some symbols and intervals. Use the output for research and paper trading validation before risking capital.

## Verified Local Start

Run:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Then open the local URL printed by Streamlit.

## Candlestick And Strategy Evaluation

The app shows a candlestick chart for a selected signal with entry, stop loss, and take profit levels. Historical strategy evaluation reports backtested win rate, setup count, profit factor, average R, and drawdown using available provider history.

Intraday history is limited by the data provider; daily and weekly views use the maximum practical history available.

## Autonomous Recommendation Journal

Enable `Registrar recomendaciones automaticamente` to store generated recommendations in a local SQLite journal. The `Registro autonomo` tab evaluates open recommendations against available market history and reports TP/SL outcomes, hit rate, average R, and hit rate by strategy and symbol.

Local journal data is stored in `data/recommendations.db` and is ignored by Git. On Streamlit Community Cloud, local file persistence may reset across redeploys or restarts; use an external database such as Supabase/Postgres for durable cloud history.
