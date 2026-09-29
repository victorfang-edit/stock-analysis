"""Download price history and compare stocks on return, risk, and trend.
usage: python analyze.py [TICKERS ...] [--years 3] [--benchmark SPY]"""
import argparse

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

TRADING_DAYS = 252


def rsi(close, period=14):
    """Relative Strength Index: 0-100, >70 'overbought', <30 'oversold' (Wilder smoothing)."""
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    return 100 - 100 / (1 + gain / loss)


def drawdown(close):
    """% below the highest price seen so far."""
    return close / close.cummax() - 1


def metrics(close, bench_returns):
    r = close.pct_change().dropna()
    years = len(r) / TRADING_DAYS
    b = bench_returns.reindex(r.index)
    return {
        "Total return": close.iloc[-1] / close.iloc[0] - 1,
        "CAGR": (close.iloc[-1] / close.iloc[0]) ** (1 / years) - 1,
        "Volatility (ann.)": r.std() * np.sqrt(TRADING_DAYS),
        "Sharpe (rf=0)": r.mean() / r.std() * np.sqrt(TRADING_DAYS),
        "Max drawdown": drawdown(close).min(),
        "Beta vs bench": r.cov(b) / b.var(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tickers", nargs="*", default=["AAPL", "MSFT", "NVDA", "JPM", "XOM"])
    ap.add_argument("--years", type=int, default=3)
    ap.add_argument("--benchmark", default="SPY")
    args = ap.parse_args()

    symbols = list(dict.fromkeys(args.tickers + [args.benchmark]))
    prices = yf.download(symbols, period=f"{args.years}y", auto_adjust=True, progress=False)["Close"].dropna()
    returns = prices.pct_change().dropna()
    print(f"Data: {prices.index[0].date()} to {prices.index[-1].date()} ({len(prices)} trading days)\n")

    table = pd.DataFrame({t: metrics(prices[t], returns[args.benchmark]) for t in symbols}).T
    table = table.sort_values("Sharpe (rf=0)", ascending=False)
    table.to_csv("docs/summary.csv", float_format="%.4f")
    pct = ["Total return", "CAGR", "Volatility (ann.)", "Max drawdown"]
    shown = table.copy()
    shown[pct] = shown[pct].map(lambda v: f"{v:+.1%}")
    shown[["Sharpe (rf=0)", "Beta vs bench"]] = shown[["Sharpe (rf=0)", "Beta vs bench"]].map(lambda v: f"{v:.2f}")
    print(shown.to_string())

    plt.style.use("seaborn-v0_8-whitegrid")

    # 1. growth of $1
    fig, ax = plt.subplots(figsize=(10, 5))
    (prices / prices.iloc[0]).plot(ax=ax, lw=1.6)
    ax.set(title=f"Growth of $1 over {args.years} years", ylabel="Value of $1", xlabel="")
    fig.tight_layout(); fig.savefig("docs/growth.png", dpi=110)

    # 2. risk vs return
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.scatter(table["Volatility (ann.)"] * 100, table["CAGR"] * 100, s=90, c="tab:blue")
    for t, row in table.iterrows():
        ax.annotate(t, (row["Volatility (ann.)"] * 100, row["CAGR"] * 100), xytext=(6, 4), textcoords="offset points")
    ax.set(title="Risk vs. return (up-left is better)", xlabel="Annualized volatility (%)", ylabel="Annual growth rate, CAGR (%)")
    fig.tight_layout(); fig.savefig("docs/risk_return.png", dpi=110)

    # 3. correlation of daily returns
    corr = returns[symbols].corr()
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(corr, cmap="RdYlGn_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(symbols)), symbols); ax.set_yticks(range(len(symbols)), symbols)
    for i in range(len(symbols)):
        for j in range(len(symbols)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Correlation of daily returns"); ax.grid(False)
    fig.tight_layout(); fig.savefig("docs/correlation.png", dpi=110)

    # 4. drawdowns
    fig, ax = plt.subplots(figsize=(10, 4.5))
    (prices.apply(drawdown) * 100).plot(ax=ax, lw=1.2)
    ax.set(title="Drawdown: % below previous peak", ylabel="%", xlabel="")
    fig.tight_layout(); fig.savefig("docs/drawdown.png", dpi=110)

    # 5. trend + momentum for the first ticker
    t = symbols[0]
    close = prices[t]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    a1.plot(close, label=f"{t} close", lw=1.3)
    a1.plot(close.rolling(50).mean(), label="50-day avg", lw=1.2)
    a1.plot(close.rolling(200).mean(), label="200-day avg", lw=1.2)
    a1.set(title=f"{t}: price trend and RSI", ylabel="$"); a1.legend()
    a2.plot(rsi(close), color="tab:purple", lw=1)
    a2.axhline(70, color="red", ls="--", lw=0.8); a2.axhline(30, color="green", ls="--", lw=0.8)
    a2.set(ylabel="RSI(14)", ylim=(0, 100))
    fig.tight_layout(); fig.savefig("docs/trend_rsi.png", dpi=110)


if __name__ == "__main__":
    main()
