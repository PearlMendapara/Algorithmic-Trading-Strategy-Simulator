"""Portfolio allocation as an unbounded knapsack problem.

Each stock i has an integer cost c_i (share price in ₹) and an integer
expected value v_i. With budget W, choose share counts q_i ≥ 0 to

    maximise   Σ v_i q_i
    subject to Σ c_i q_i ≤ W.

Two solvers are provided:

* greedy_allocation — sort by value/cost ratio and buy as many shares of each
  stock as the remaining budget allows. O(n log n + n) time, O(n) space.
  Fast, but not always optimal.
* dp_allocation — dynamic programming over budgets 0..W with the recurrence
  dp[w] = max(dp[w], dp[w − c_i] + v_i). O(n·W) time, O(W) space.
  Always optimal.
"""

from __future__ import annotations

from dataclasses import dataclass, field

Stock = tuple[str, int, int]          # (name, cost, value)


@dataclass
class Allocation:
    approach: str
    quantities: dict[str, int]
    total_value: int
    spent: int
    budget: int
    extra: dict = field(default_factory=dict)

    @property
    def remaining(self) -> int:
        return self.budget - self.spent

    @property
    def selected(self) -> list[str]:
        return [name for name, q in self.quantities.items() if q > 0]


def _validate(stocks: list[Stock], budget: int) -> None:
    if budget < 0:
        raise ValueError("budget must be non-negative")
    for name, cost, value in stocks:
        if cost <= 0:
            raise ValueError(f"{name}: cost must be a positive integer, got {cost}")
        if value < 0:
            raise ValueError(f"{name}: value must be non-negative, got {value}")


def greedy_allocation(stocks: list[Stock], budget: int) -> Allocation:
    """Buy the best value/cost stock as much as possible, then the next, and so on."""
    _validate(stocks, budget)
    quantities = {name: 0 for name, _, _ in stocks}
    remaining, total_value = budget, 0

    for name, cost, value in sorted(stocks, key=lambda s: s[2] / s[1], reverse=True):
        qty = remaining // cost
        if qty:
            quantities[name] = qty
            total_value += qty * value
            remaining -= qty * cost

    return Allocation("Greedy", quantities, total_value, budget - remaining, budget)


def dp_allocation(stocks: list[Stock], budget: int) -> Allocation:
    """Optimal allocation via unbounded-knapsack dynamic programming.

    dp[w]     = best total value achievable with total cost ≤ w
    choice[w] = index of the stock added last to reach dp[w] (−1 if none)

    Storing only the last choice per budget keeps memory at O(W); the full
    allocation is recovered by walking choice[] back from w = budget.
    """
    _validate(stocks, budget)
    dp = [0] * (budget + 1)
    choice = [-1] * (budget + 1)

    for w in range(1, budget + 1):
        best, best_i = dp[w], -1
        for i, (_, cost, value) in enumerate(stocks):
            if cost <= w and dp[w - cost] + value > best:
                best, best_i = dp[w - cost] + value, i
        dp[w], choice[w] = best, best_i

    quantities = {name: 0 for name, _, _ in stocks}
    w, spent = budget, 0
    while w > 0:
        i = choice[w]
        if i == -1:
            w -= 1             # no stock ends exactly here; value comes from a smaller budget
            continue
        name, cost, _ = stocks[i]
        quantities[name] += 1
        spent += cost
        w -= cost

    return Allocation("Dynamic Programming", quantities, dp[budget], spent, budget)
