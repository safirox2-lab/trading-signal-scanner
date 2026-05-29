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
