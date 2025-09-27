"""Excel report with prediction, allocation tables and embedded charts."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl
import pandas as pd
from openpyxl.drawing.image import Image

from .optimization import Allocation


def plot_comparison(greedy: Allocation, dp: Allocation, out_dir: Path) -> Path:
    """Bar chart of total expected value, greedy vs DP."""
    out_dir.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar([greedy.approach, dp.approach], [greedy.total_value, dp.total_value],
                  color=["#3498db", "#2ecc71"], width=0.6)
    ax.set_title("Portfolio Optimization Comparison", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Expected Value (₹)", fontsize=12)
    ax.grid(axis="y", alpha=0.3)
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h, f"₹{int(h):,}",
                ha="center", va="bottom", fontsize=11)
    path = out_dir / "portfolio_comparison.png"
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    return path


def _row(a: Allocation) -> dict:
    return {
        "Approach": a.approach,
        "Selected Stocks": ", ".join(a.selected),
        "Total Value": a.total_value,
        "Spent": a.spent,
        "Remaining Budget": a.remaining,
        "Runtime (s)": round(a.extra.get("runtime_s", float("nan")), 4),
    }


def save_to_excel(prediction: dict, greedy: Allocation, dp: Allocation,
                  prediction_plot: Path | None, out_path: Path) -> Path:
    """Write the three result sheets and embed both charts."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        pd.DataFrame([prediction]).to_excel(writer, sheet_name="Prediction", index=False)
        pd.DataFrame([_row(greedy), _row(dp)]).to_excel(writer, sheet_name="Portfolio", index=False)
        pd.DataFrame({
            "Company": list(greedy.quantities),
            "Greedy Quantity": list(greedy.quantities.values()),
            "DP Quantity": [dp.quantities[c] for c in greedy.quantities],
        }).to_excel(writer, sheet_name="Stock Quantities", index=False)

    wb = openpyxl.load_workbook(out_path)
    if prediction_plot is not None:
        img = Image(str(prediction_plot))
        img.width, img.height = 600, 400
        wb["Prediction"].add_image(img, "F2")
    img = Image(str(plot_comparison(greedy, dp, out_path.parent)))
    img.width, img.height = 500, 350
    wb["Portfolio"].add_image(img, "H2")
    wb.save(out_path)
    return out_path
