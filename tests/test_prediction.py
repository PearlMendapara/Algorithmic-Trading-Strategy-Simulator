"""Tests for the linear-trend price model.

Run with:  pytest -q
"""

import numpy as np
import pandas as pd
import pytest

from simulator.prediction import fit_and_predict


def linear_series(start=100.0, slope=2.0, days=60):
    index = pd.date_range("2025-01-01", periods=days, freq="D")
    return pd.Series(start + slope * np.arange(days), index=index)


def test_recovers_exact_linear_trend():
    close = linear_series(start=100.0, slope=2.0, days=60)
    result = fit_and_predict(close, days_ahead=1)
    assert result["Daily Trend"] == pytest.approx(2.0)
    assert result["Current Price"] == pytest.approx(218.0)
    assert result["Predicted Price"] == pytest.approx(220.0)
    assert result["Test MSE"] == pytest.approx(0.0, abs=1e-9)


def test_days_ahead_extrapolates_further():
    close = linear_series(slope=-1.5)
    one = fit_and_predict(close, days_ahead=1)["Predicted Price"]
    five = fit_and_predict(close, days_ahead=5)["Predicted Price"]
    assert five - one == pytest.approx(-6.0)


def test_uses_calendar_days_not_row_positions():
    # Weekday-only index: the gap over each weekend is 3 calendar days.
    index = pd.bdate_range("2025-01-06", periods=40)
    days = (index - index[0]).days.to_numpy()
    close = pd.Series(50.0 + 0.5 * days, index=index)
    result = fit_and_predict(close, days_ahead=1)
    assert result["Daily Trend"] == pytest.approx(0.5)
