"""Algorithmic Trading Strategy Simulator — command-line entry point.

Examples
--------
Live data from Yahoo Finance (interactive prompts):
    python main.py

Live data, no prompts:
    python main.py --company TCS --budget 500000

Offline, with prices from a JSON file (no network needed; skips prediction):
    python main.py --budget 500000 --prices examples/sample_prices.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from simulator.config import COMPANIES
from simulator.optimization import Stock, dp_allocation, greedy_allocation, Allocation

OUT_DIR = Path("outputs")


def build_stocks(prices: dict[str, float]) -> list[Stock]:
    """Turn prices into knapsack items: cost = price, value = price × (1 + return%)."""
    stocks = []
    for name, (ticker, return_pct) in COMPANIES.items():
        cost = int(round(prices.get(name, 0)))
        if cost <= 0:
            print(f"  Skipping {name}: no price available")
            continue
        stocks.append((name, cost, int(cost * (1 + return_pct / 100))))
    return stocks


def timed(solver, stocks: list[Stock], budget: int) -> Allocation:
    start = time.perf_counter()
    result = solver(stocks, budget)
    result.extra["runtime_s"] = time.perf_counter() - start
    return result


def print_allocation(a: Allocation) -> None:
    print(f"\n--- {a.approach} ---")
    for name, qty in a.quantities.items():
        if qty:
            print(f"  {name}: {qty} shares")
    print(f"  Total expected value : ₹{a.total_value:,}")
    print(f"  Spent / remaining    : ₹{a.spent:,} / ₹{a.remaining:,}")
    print(f"  Runtime              : {a.extra['runtime_s']:.4f} s")


def ask_company() -> str:
    while True:
        choice = input(f"\nCompany for price prediction ({', '.join(COMPANIES)}): ").strip().upper()
        if choice in COMPANIES:
            return choice
        print("  Invalid choice. Please select from the list.")


def ask_budget() -> int:
    while True:
        try:
            budget = int(input("\nBudget for portfolio optimization (₹): "))
            if budget > 0:
                return budget
            print("  Budget must be positive.")
        except ValueError:
            print("  Please enter a whole number.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Algorithmic Trading Strategy Simulator")
    parser.add_argument("--company", choices=list(COMPANIES), type=str.upper,
                        help="company to forecast (live mode only)")
    parser.add_argument("--budget", type=int, help="investment budget in ₹")
    parser.add_argument("--prices", type=Path,
                        help="JSON file of {company: price}; runs offline and skips prediction")
    parser.add_argument("--no-excel", action="store_true", help="skip the Excel report")
    args = parser.parse_args()
    if args.budget is not None and args.budget <= 0:
        parser.error("--budget must be a positive whole number")

    print("=" * 60)
    print("ALGORITHMIC TRADING STRATEGY SIMULATOR")
    print("=" * 60)

    prediction, prediction_plot = None, None
    if args.prices:
        try:
            prices = {name: float(p) for name, p in json.loads(args.prices.read_text()).items()}
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            parser.error(f"could not read prices from {args.prices}: {exc}")
        print(f"\nUsing prices from {args.prices}")
    else:
        from simulator.data import fetch_history, get_current_prices
        from simulator.prediction import fit_and_predict, plot_prediction

        print("\nFetching current prices from Yahoo Finance…")
        prices = get_current_prices()

    print("\nCurrent prices:")
    for name, price in prices.items():
        print(f"  {name}: ₹{price:,.2f}")

    budget = args.budget or ask_budget()

    if not args.prices:
        company = args.company or ask_company()
        ticker = COMPANIES[company][0]
        print("\n" + "=" * 60)
        print(f"STOCK PRICE PREDICTION — {company}")
        print("=" * 60)
        close = fetch_history(ticker, period="90d")
        prediction = {"Stock": ticker, **fit_and_predict(close, days_ahead=1)}
        prediction_plot = plot_prediction(close, prediction["Predicted Price"], ticker, 1, OUT_DIR)
        print(f"  Current price       : ₹{prediction['Current Price']:,.2f}")
        print(f"  Predicted (1 day)   : ₹{prediction['Predicted Price']:,.2f}")
        print(f"  Test MSE (last 20%) : {prediction['Test MSE']:.2f}")

    print("\n" + "=" * 60)
    print(f"PORTFOLIO OPTIMIZATION (budget ₹{budget:,})")
    print("=" * 60)
    stocks = build_stocks(prices)
    greedy = timed(greedy_allocation, stocks, budget)
    dp = timed(dp_allocation, stocks, budget)
    print_allocation(greedy)
    print_allocation(dp)

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)
    diff = dp.total_value - greedy.total_value
    if diff > 0:
        print(f"  DP is better by ₹{diff:,} ({diff / greedy.total_value * 100:.2f}%)")
    else:
        print("  Greedy matches the optimal DP allocation")

    if not args.no_excel:
        from simulator.reporting import save_to_excel
        path = save_to_excel(prediction or {"Mode": "offline — no prediction"},
                             greedy, dp, prediction_plot, OUT_DIR / "trading_simulator_results.xlsx")
        print(f"\nResults saved to {path}")


if __name__ == "__main__":
    main()
