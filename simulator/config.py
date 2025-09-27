"""Universe of NSE stocks the simulator trades, with assumed expected returns."""

# name: (Yahoo Finance ticker, assumed expected return in % over the holding period)
#
# These returns are fixed modelling assumptions, not forecasts. Each stock's
# "value" in the knapsack is price × (1 + return / 100). Edit them to test
# other scenarios.
COMPANIES: dict[str, tuple[str, float]] = {
    "TCS":      ("TCS.NS",       50),
    "HDFC":     ("HDFCBANK.NS",  45),
    "HUL":      ("HINDUNILVR.NS", 30),
    "RELIANCE": ("RELIANCE.NS",  35),
    "MARUTI":   ("MARUTI.NS",    40),
}
