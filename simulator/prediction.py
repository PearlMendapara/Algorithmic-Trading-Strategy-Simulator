"""Next-day price prediction with a linear trend model.

The model fits  price = m · day + b  on recent closing prices. Time complexity
is O(n) in the number of trading days used.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error


def fit_and_predict(close: pd.Series, days_ahead: int = 1, test_size: float = 0.2) -> dict:
    """Fit a linear trend to `close` and predict `days_ahead` calendar days ahead.

    The train/test split is chronological: the model is trained on the
    earliest (1 - test_size) share of days and evaluated on the most recent
    ones, so the test error measures genuine out-of-sample forecasting.
    """
    if len(close) < 5:
        raise ValueError(f"need at least 5 closing prices to fit a trend, got {len(close)}")
    days = (close.index - close.index.min()).days.to_numpy().reshape(-1, 1)
    prices = close.to_numpy()

    split = int(len(prices) * (1 - test_size))
    model = LinearRegression().fit(days[:split], prices[:split])
    test_mse = mean_squared_error(prices[split:], model.predict(days[split:]))

    # Refit on all data for the final forecast
    model.fit(days, prices)
    future_day = days[-1][0] + days_ahead
    predicted = float(model.predict(np.array([[future_day]]))[0])

    return {
        "Current Price": float(prices[-1]),
        "Predicted Price": predicted,
        "Daily Trend": float(model.coef_[0]),
        "Test MSE": float(test_mse),
    }


def plot_prediction(close: pd.Series, predicted: float, ticker: str,
                    days_ahead: int, out_dir: Path) -> Path:
    """Plot price history with the forecast point; return the image path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(close.index, close.values, label="Historical prices")
    plt.scatter(close.index[-1] + pd.Timedelta(days=days_ahead), predicted,
                color="red", s=100, zorder=5, label=f"{days_ahead}-day prediction")
    plt.title(f"{ticker} Price Prediction ({days_ahead} day)")
    plt.xlabel("Date")
    plt.ylabel("Price (₹)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = out_dir / f"{ticker}_prediction.png"
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close()
    return path
