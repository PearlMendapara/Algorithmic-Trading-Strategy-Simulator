"""Correctness tests for the portfolio optimisers.

Run with:  pytest -q
"""

import itertools
import random

import pytest

from simulator.optimization import dp_allocation, greedy_allocation


def brute_force(stocks, budget):
    """Exhaustive search over all share counts — the ground truth for small cases."""
    ranges = [range(budget // cost + 1) for _, cost, _ in stocks]
    best = 0
    for qty in itertools.product(*ranges):
        spent = sum(q * c for q, (_, c, _) in zip(qty, stocks))
        if spent <= budget:
            best = max(best, sum(q * v for q, (_, _, v) in zip(qty, stocks)))
    return best


def check_consistent(result, stocks, budget):
    """Quantities must reproduce the reported value and respect the budget."""
    by_name = {name: (cost, value) for name, cost, value in stocks}
    spent = sum(q * by_name[n][0] for n, q in result.quantities.items())
    value = sum(q * by_name[n][1] for n, q in result.quantities.items())
    assert spent == result.spent
    assert value == result.total_value
    assert spent <= budget
    assert all(q >= 0 for q in result.quantities.values())


def test_greedy_is_suboptimal_on_classic_counterexample():
    # A has the better ratio (1.5 vs 1.4) but only one share fits;
    # two shares of B use the whole budget and are worth more.
    stocks = [("A", 6, 9), ("B", 5, 7)]
    greedy = greedy_allocation(stocks, 10)
    dp = dp_allocation(stocks, 10)
    assert greedy.total_value == 9
    assert dp.total_value == 14
    assert dp.quantities == {"A": 0, "B": 2}


@pytest.mark.parametrize("seed", range(200))
def test_dp_matches_brute_force(seed):
    rng = random.Random(seed)
    n = rng.randint(1, 4)
    stocks = [(f"S{i}", rng.randint(1, 15), rng.randint(0, 30)) for i in range(n)]
    budget = rng.randint(0, 40)

    dp = dp_allocation(stocks, budget)
    greedy = greedy_allocation(stocks, budget)

    assert dp.total_value == brute_force(stocks, budget)
    assert greedy.total_value <= dp.total_value
    check_consistent(dp, stocks, budget)
    check_consistent(greedy, stocks, budget)


def test_budget_smaller_than_every_price():
    stocks = [("A", 50, 60), ("B", 70, 90)]
    for solver in (greedy_allocation, dp_allocation):
        result = solver(stocks, 40)
        assert result.total_value == 0
        assert result.remaining == 40


def test_zero_budget():
    assert dp_allocation([("A", 3, 4)], 0).total_value == 0


def test_rejects_non_positive_cost():
    with pytest.raises(ValueError):
        dp_allocation([("A", 0, 5)], 10)
    with pytest.raises(ValueError):
        greedy_allocation([("A", -2, 5)], 10)


def test_rejects_negative_budget():
    for solver in (greedy_allocation, dp_allocation):
        with pytest.raises(ValueError):
            solver([("A", 3, 4)], -1)


def test_rejects_negative_value():
    for solver in (greedy_allocation, dp_allocation):
        with pytest.raises(ValueError):
            solver([("A", 3, -4)], 10)
