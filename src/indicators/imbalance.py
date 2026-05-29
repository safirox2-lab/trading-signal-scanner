import pandas as pd


def fair_value_gaps(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, float | str | None]] = []
    for index in range(len(df)):
        if index < 2:
            rows.append({"type": None, "lower": None, "upper": None})
            continue
        first = df.iloc[index - 2]
        third = df.iloc[index]
        if float(first["high"]) < float(third["low"]):
            rows.append({"type": "bullish", "lower": float(first["high"]), "upper": float(third["low"])})
        elif float(first["low"]) > float(third["high"]):
            rows.append({"type": "bearish", "lower": float(third["high"]), "upper": float(first["low"])})
        else:
            rows.append({"type": None, "lower": None, "upper": None})
    return pd.DataFrame(rows, index=df.index)
