"""Market data access through Yahoo Finance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from .config import COMPANIES


def _close_series(data: pd.DataFrame) -> pd.Series:
    """Return the Close column as a 1-D Series.

    Recent yfinance versions return MultiIndex columns (field, ticker) even for
    a single ticker, so data["Close"] can be a one-column DataFrame.
    """
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.astype(float)


def fetch_history(ticker: str, period: str) -> pd.Series:
    """Daily closing prices for `ticker` over `period` (e.g. "90d")."""
    data = yf.download(ticker, period=period, interval="1d",
                       auto_adjust=False, progress=False)
    if data.empty:
        raise ValueError(f"No data found for ticker {ticker}")
    return _close_series(data).dropna()


def get_current_prices() -> dict[str, float]:
    """Latest close for every company in the universe (0 if unavailable)."""
    prices = {}
    for name, (ticker, _) in COMPANIES.items():
        try:
            prices[name] = float(fetch_history(ticker, period="5d").iloc[-1])
        except ValueError:
            prices[name] = 0.0
    return prices
