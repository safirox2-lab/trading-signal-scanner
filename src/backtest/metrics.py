def max_drawdown(equity_curve: list[float]) -> float:
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = max(worst, (peak - value) / peak)
    return round(worst, 4)


def summarize_trades(r_multiples: list[float]) -> dict[str, float]:
    trades = len(r_multiples)
    wins = [value for value in r_multiples if value > 0]
    losses = [value for value in r_multiples if value < 0]
    gross_win = sum(wins)
    gross_loss = abs(sum(losses))
    return {
        "trades": trades,
        "win_rate": round((len(wins) / trades) * 100, 2) if trades else 0.0,
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss else float("inf"),
        "average_r": round(sum(r_multiples) / trades, 2) if trades else 0.0,
    }
