#!/usr/bin/env python3
"""
plot_tuning_results.py — Generate presentation-ready visualizations.

Plots generated:
1. training_heatmap_score_diff.png — Score diff across c × opponent
2. training_winrate_by_c.png — Win rate by c (bar chart)
3. training_score_diff_by_c.png — Avg score diff by c (bar chart)
4. bandit_learning_curve.png — Bandit reward over episodes
5. bandit_q_values_by_c.png — Final Q-values for each c
6. test_comparison.png — Best c vs baselines on test set
7. generalization_heatmap.png — Win rate across c × test opponent

Usage:
    python3 plot_tuning_results.py
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
GRID_RESULTS = os.path.join(ROOT, "results", "tuning", "grid", "tuning_results.csv")
GRID_SUMMARY = os.path.join(ROOT, "results", "tuning", "grid", "tuning_summary.csv")
BANDIT_RESULTS = os.path.join(ROOT, "results", "tuning", "bandit", "bandit_results.csv")
BANDIT_SUMMARY = os.path.join(ROOT, "results", "tuning", "bandit", "bandit_summary.csv")
TEST_RESULTS = os.path.join(ROOT, "results", "testing", "test_results.csv")
TEST_SUMMARY = os.path.join(ROOT, "results", "testing", "test_summary.csv")
FIGURE_DIR = os.path.join(ROOT, "results", "figures")


def try_import(module_name: str):
    """Try to import a module and exit gracefully if missing."""
    try:
        return __import__(module_name)
    except ImportError:
        print(f"ERROR: {module_name} not installed")
        print(f"Install with: pip install {module_name}")
        sys.exit(1)


def plot_training_heatmap_score_diff():
    """Plot score_diff across c × opponent (grid results)."""
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    
    if not os.path.isfile(GRID_RESULTS):
        print(f"⚠ Skipping training_heatmap (no {GRID_RESULTS})")
        return

    df = pd.read_csv(GRID_RESULTS)
    pivot = df.pivot_table(values="score_diff", index="opponent", columns="c", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=-10, vmax=10)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{c:.1f}" for c in pivot.columns], fontsize=10)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)

    ax.set_xlabel("Aggression Parameter (c)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Training Opponent", fontsize=12, fontweight="bold")
    ax.set_title("Grid Search: Avg Score Diff by c and Opponent", fontsize=14, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Score Diff (Agent - Opponent)", fontsize=11)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not np.isnan(val):
                text_color = "white" if abs(val) > 5 else "black"
                ax.text(j, i, f"{val:.1f}", ha="center", va="center",
                        color=text_color, fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "training_heatmap_score_diff.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_training_winrate_by_c():
    """Bar chart of win rate by c."""
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(GRID_SUMMARY):
        print(f"⚠ Skipping training_winrate (no {GRID_SUMMARY})")
        return

    df = pd.read_csv(GRID_SUMMARY)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df["c"], df["win_rate"], width=0.08, color="steelblue", edgecolor="black", linewidth=1.5)

    # Highlight best
    best_idx = df["win_rate"].idxmax()
    bars[best_idx].set_color("gold")
    bars[best_idx].set_edgecolor("red")
    bars[best_idx].set_linewidth(2)

    ax.set_xlabel("Aggression Parameter (c)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Win Rate", fontsize=12, fontweight="bold")
    ax.set_title("Grid Search: Win Rate by Aggression Parameter", fontsize=14, fontweight="bold")
    ax.set_ylim([0, 1.0])
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    for i, (c, wr) in enumerate(zip(df["c"], df["win_rate"])):
        ax.text(c, wr + 0.02, f"{wr:.1%}", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "training_winrate_by_c.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_training_score_diff_by_c():
    """Bar chart of avg score diff by c."""
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(GRID_SUMMARY):
        print(f"⚠ Skipping training_score_diff (no {GRID_SUMMARY})")
        return

    df = pd.read_csv(GRID_SUMMARY)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df["c"], df["avg_score_diff"], width=0.08, 
                   color=["red" if x < 0 else "green" for x in df["avg_score_diff"]],
                   edgecolor="black", linewidth=1.5)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
    ax.set_xlabel("Aggression Parameter (c)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Avg Score Diff (Agent - Opponent)", fontsize=12, fontweight="bold")
    ax.set_title("Grid Search: Average Score Differential by Aggression", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    for c, sd in zip(df["c"], df["avg_score_diff"]):
        y = sd + (0.5 if sd > 0 else -0.5)
        ax.text(c, y, f"{sd:.1f}", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "training_score_diff_by_c.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_bandit_learning_curve():
    """Line plot of bandit reward (cumulative average) over episodes."""
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(BANDIT_RESULTS):
        print(f"⚠ Skipping bandit_learning_curve (no {BANDIT_RESULTS})")
        return

    df = pd.read_csv(BANDIT_RESULTS)
    df = df.sort_values("episode")

    # Compute rolling average
    df["cumsum_reward"] = df["score_diff"].cumsum()
    df["avg_reward"] = df["cumsum_reward"] / (df.index + 1)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["episode"], df["avg_reward"], linewidth=2.5, color="steelblue", label="Cumulative Avg Reward")
    ax.scatter(df["episode"], df["score_diff"], alpha=0.3, s=30, color="lightblue", label="Per-Episode Reward")

    ax.set_xlabel("Episode", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score Diff (Agent - Opponent)", fontsize=12, fontweight="bold")
    ax.set_title("Bandit Learning: Cumulative Average Reward Over Episodes", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(fontsize=11)

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "bandit_learning_curve.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_bandit_q_values():
    """Bar chart of final Q-values for each c."""
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(BANDIT_SUMMARY):
        print(f"⚠ Skipping bandit_q_values (no {BANDIT_SUMMARY})")
        return

    df = pd.read_csv(BANDIT_SUMMARY)

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(df["c"], df["final_q_value"], width=0.08,
                   color=["red" if x < 0 else "green" for x in df["final_q_value"]],
                   edgecolor="black", linewidth=1.5)

    best_idx = df["final_q_value"].idxmax()
    bars[best_idx].set_color("gold")
    bars[best_idx].set_edgecolor("red")
    bars[best_idx].set_linewidth(2)

    ax.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
    ax.set_xlabel("Aggression Parameter (c)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Learned Q-Value", fontsize=12, fontweight="bold")
    ax.set_title("Bandit: Final Q-Values (Estimated Arm Values)", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3, linestyle="--")

    for c, q in zip(df["c"], df["final_q_value"]):
        y = q + (0.5 if q > 0 else -0.5)
        ax.text(c, y, f"{q:.2f}", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "bandit_q_values_by_c.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_test_comparison():
    """Bar chart comparing test performance of selected c vs baselines."""
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(TEST_SUMMARY):
        print(f"⚠ Skipping test_comparison (no {TEST_SUMMARY})")
        return

    df = pd.read_csv(TEST_SUMMARY)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Win rate
    colors = ["steelblue"] * len(df)
    labels = df["c_label"].tolist()
    for i, label in enumerate(labels):
        if "grid" in label.lower():
            colors[i] = "gold"
        elif "bandit" in label.lower():
            colors[i] = "lightcoral"

    bars1 = ax1.bar(range(len(df)), df["win_rate"], color=colors, edgecolor="black", linewidth=1.5)
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
    ax1.set_ylabel("Win Rate", fontsize=12, fontweight="bold")
    ax1.set_title("Test Set: Win Rate Comparison", fontsize=13, fontweight="bold")
    ax1.set_ylim([0, 1.0])
    ax1.grid(axis="y", alpha=0.3, linestyle="--")

    for i, wr in enumerate(df["win_rate"]):
        ax1.text(i, wr + 0.02, f"{wr:.1%}", ha="center", fontsize=9, fontweight="bold")

    # Avg score diff
    bars2 = ax2.bar(range(len(df)), df["avg_score_diff"],
                    color=["red" if x < 0 else "green" for x in df["avg_score_diff"]],
                    edgecolor="black", linewidth=1.5)
    ax2.axhline(y=0, color="black", linestyle="-", linewidth=0.8)
    ax2.set_xticks(range(len(df)))
    ax2.set_xticklabels(labels, rotation=45, ha="right", fontsize=10)
    ax2.set_ylabel("Avg Score Diff", fontsize=12, fontweight="bold")
    ax2.set_title("Test Set: Average Score Differential", fontsize=13, fontweight="bold")
    ax2.grid(axis="y", alpha=0.3, linestyle="--")

    for i, sd in enumerate(df["avg_score_diff"]):
        y = sd + (0.5 if sd > 0 else -0.5)
        ax2.text(i, y, f"{sd:.1f}", ha="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "test_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def plot_generalization_heatmap():
    """Heatmap of win rate across c × test opponent (testing results)."""
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd

    if not os.path.isfile(TEST_RESULTS):
        print(f"⚠ Skipping generalization_heatmap (no {TEST_RESULTS})")
        return

    df = pd.read_csv(TEST_RESULTS)
    pivot = df.pivot_table(values="win", index="opponent", columns="c", aggfunc="mean")

    fig, ax = plt.subplots(figsize=(12, 5))
    im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([f"{c:.2f}" for c in pivot.columns], fontsize=10, rotation=45)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=11)

    ax.set_xlabel("Aggression Parameter (c)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Test Opponent", fontsize=12, fontweight="bold")
    ax.set_title("Generalization: Win Rate by c and Test Opponent", fontsize=14, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Win Rate", fontsize=11)

    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.iloc[i, j]
            if not np.isnan(val):
                text_color = "white" if val > 0.5 else "black"
                ax.text(j, i, f"{val:.1%}", ha="center", va="center",
                        color=text_color, fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(FIGURE_DIR, "generalization_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    print(f"✓ {path}")
    plt.close()


def main():
    print("═" * 80)
    print("GENERATING PRESENTATION PLOTS")
    print("═" * 80)

    # Check imports
    try_import("matplotlib")
    try_import("pandas")
    try_import("numpy")

    os.makedirs(FIGURE_DIR, exist_ok=True)

    print("\nGenerating plots...\n")

    plot_training_heatmap_score_diff()
    plot_training_winrate_by_c()
    plot_training_score_diff_by_c()
    plot_bandit_learning_curve()
    plot_bandit_q_values()
    plot_test_comparison()
    plot_generalization_heatmap()

    print(f"\n✓ All plots saved to: {FIGURE_DIR}")
    print(f"\nNext step: python3 experiment_summary.py")


if __name__ == "__main__":
    main()
