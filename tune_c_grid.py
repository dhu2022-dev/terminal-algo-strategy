#!/usr/bin/env python3
"""
tune_c_grid.py — Grid search parameter tuning for aggression parameter c.

This script:
1. Loads experiment_config.json
2. For each c value
3. For each training opponent
4. Runs N games locally using engine.jar
5. Parses replays and saves per-match metrics
6. Aggregates and selects best c

Outputs:
- results/tuning/grid/tuning_results.csv (per-match)
- results/tuning/grid/tuning_summary.csv (aggregated by c)
- results/tuning/grid/best_c.json (selected c with metadata)

Usage:
    python3 tune_c_grid.py
"""

import argparse
import csv
import json
import glob
import os
import re
import shutil
import stat
import subprocess
import sys
import textwrap
from collections import defaultdict

ROOT = os.path.dirname(os.path.abspath(__file__))
ALGO_SRC = os.path.join(ROOT, "python-algo")
ENGINE = os.path.join(ROOT, "engine.jar")
CONFIG = os.path.join(ROOT, "experiment_config.json")
OUTPUT_DIR = os.path.join(ROOT, "results", "tuning", "grid")
REPLAY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "replays")


def load_config():
    """Load experiment configuration."""
    with open(CONFIG, "r") as f:
        return json.load(f)


def make_agent_dir(c_value: float, opponent: str, run_id: int) -> str:
    """Create temp agent directory with specific aggression value."""
    name = f"grid_c{c_value:.2f}_{opponent}_r{run_id}"
    dest = os.path.join(ROOT, ".grid_tmp", name)
    os.makedirs(dest, exist_ok=True)

    # Symlink shared code
    for dirname in ("gamelib", "strategies"):
        src = os.path.join(ALGO_SRC, dirname)
        dst = os.path.join(dest, dirname)
        if os.path.exists(dst):
            os.remove(dst)
        if os.path.isdir(src):
            os.symlink(src, dst)

    # Copy entry points
    for fname in ("algo_strategy.py", "algo.json"):
        src = os.path.join(ALGO_SRC, fname)
        dst = os.path.join(dest, fname)
        shutil.copy2(src, dst)

    # Write run.sh with AGGRESSION
    run_sh = os.path.join(dest, "run.sh")
    with open(run_sh, "w") as f:
        f.write(textwrap.dedent(f"""\
            #!/bin/bash
            export AGGRESSION={c_value:.4f}
            DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
            ${{PYTHON_CMD:-python3}} -u "$DIR/algo_strategy.py"
        """))
    os.chmod(run_sh, os.stat(run_sh).st_mode | stat.S_IEXEC)

    return dest


def get_opponent_path(opponent_name: str) -> str:
    """Get path to opponent run.sh."""
    return os.path.join(ROOT, "opponents", opponent_name, "run.sh")


def find_latest_replay() -> str | None:
    """Find the most recently created .replay file."""
    pattern = os.path.join(ROOT, "replays", "*.replay")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def run_match(agent_dir: str, opponent_path: str, c_value: float, 
              opponent: str, run_id: int) -> dict | None:
    """Run a single match and return result dict."""
    print(f"    c={c_value:.2f}  opp={opponent:20s}  run={run_id}...", 
          end=" ", flush=True)

    try:
        result = subprocess.run(
            ["java", "-jar", ENGINE, "work",
             os.path.join(agent_dir, "run.sh"),
             opponent_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"FAILED")
            return None

        # Find replay
        replay = find_latest_replay()
        if not replay:
            print(f"NO REPLAY")
            return None

        # Parse replay
        row = parse_replay(replay, c_value, opponent, run_id)

        # Move replay to organized folder
        if row:
            dest_folder = os.path.join(REPLAY_OUTPUT_DIR, f"c_{c_value:.2f}", opponent)
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, f"run_{run_id}.replay")
            shutil.move(replay, dest_path)
            row["replay_path"] = dest_path
            print(f"OK")
            return row
        else:
            print(f"PARSE FAILED")
            return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None


def parse_replay(path: str, c_value: float, opponent: str, run_id: int) -> dict | None:
    """Parse a replay file and extract metrics."""
    try:
        with open(path, "r") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception as e:
        return None

    end_stats = None
    for line in lines:
        try:
            obj = json.loads(line)
            if "endStats" in obj:
                end_stats = obj["endStats"]
        except json.JSONDecodeError:
            continue

    if end_stats is None:
        return None

    winner_id = end_stats.get("winner", -1)
    duration = end_stats.get("turns", 0)
    p1 = end_stats.get("player1", {})
    p2 = end_stats.get("player2", {})

    agent_score = p1.get("points_scored", 0)
    opponent_score = p2.get("points_scored", 0)
    win = 1 if winner_id == 1 else 0

    return {
        "c": c_value,
        "opponent": opponent,
        "run_id": run_id,
        "agent_score": agent_score,
        "opponent_score": opponent_score,
        "score_diff": agent_score - opponent_score,
        "win": win,
        "turns": duration,
    }


def select_best_c(summary_dict: dict) -> tuple[float, dict]:
    """Select best c based on avg_score_diff, with tie-breaking."""
    best_c = None
    best_score_diff = -float('inf')
    best_row = None

    for c in sorted(summary_dict.keys()):
        row = summary_dict[c]
        score_diff = row["avg_score_diff"]

        # Tie-break: higher win_rate, lower variance, closer to 0.5
        if score_diff > best_score_diff or (
            score_diff == best_score_diff and 
            row["win_rate"] > best_row.get("win_rate", 0)
        ):
            best_score_diff = score_diff
            best_c = c
            best_row = row

    return best_c, best_row


def main():
    print("═" * 80)
    print("GRID SEARCH PARAMETER TUNING")
    print("═" * 80)

    # Load config
    config = load_config()
    c_values = config["c_values"]
    train_opponents = config["train_opponents"]
    games_per = config["games_per_c_per_opponent"]

    print(f"\nConfiguration:")
    print(f"  c values: {c_values}")
    print(f"  opponents: {train_opponents}")
    print(f"  games per combo: {games_per}")
    print(f"  Total matches: {len(c_values) * len(train_opponents) * games_per}\n")

    # Pre-flight checks
    if not os.path.isfile(ENGINE):
        print(f"ERROR: engine.jar not found")
        sys.exit(1)
    for opp in train_opponents:
        opp_path = get_opponent_path(opp)
        if not os.path.isfile(opp_path):
            print(f"ERROR: opponent {opp} not found at {opp_path}")
            sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPLAY_OUTPUT_DIR, exist_ok=True)

    # Run grid search
    results = []
    for c in c_values:
        print(f"\n[c = {c:.2f}]")
        for opponent in train_opponents:
            opponent_path = get_opponent_path(opponent)
            for run_id in range(1, games_per + 1):
                agent_dir = make_agent_dir(c, opponent, run_id)
                row = run_match(agent_dir, opponent_path, c, opponent, run_id)
                if row:
                    results.append(row)

    # Cleanup temp dirs
    tmp_dir = os.path.join(ROOT, ".grid_tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    # Write per-match CSV
    if not results:
        print("ERROR: No results collected")
        sys.exit(1)

    csv_path = os.path.join(OUTPUT_DIR, "tuning_results.csv")
    fieldnames = ["c", "opponent", "run_id", "agent_score", "opponent_score",
                  "score_diff", "win", "turns", "replay_path"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✓ Per-match results: {csv_path}")

    # Aggregate by c
    by_c = defaultdict(list)
    for row in results:
        by_c[row["c"]].append(row)

    summary_dict = {}
    summary_rows = []
    for c in sorted(by_c.keys()):
        rows = by_c[c]
        n = len(rows)
        wins = sum(1 for r in rows if r["win"])
        avg_score_diff = sum(r["score_diff"] for r in rows) / n
        avg_agent_score = sum(r["agent_score"] for r in rows) / n
        avg_opponent_score = sum(r["opponent_score"] for r in rows) / n
        avg_turns = sum(r["turns"] for r in rows) / n

        summary_row = {
            "c": c,
            "num_games": n,
            "win_rate": round(wins / n, 3),
            "avg_score_diff": round(avg_score_diff, 2),
            "avg_agent_score": round(avg_agent_score, 2),
            "avg_opponent_score": round(avg_opponent_score, 2),
            "avg_turns": round(avg_turns, 1),
        }
        summary_dict[c] = summary_row
        summary_rows.append(summary_row)

    summary_csv = os.path.join(OUTPUT_DIR, "tuning_summary.csv")
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"✓ Summary by c: {summary_csv}")

    # Select best c
    best_c, best_row = select_best_c(summary_dict)
    best_c_dict = {
        "c_best": best_c,
        "avg_score_diff": best_row["avg_score_diff"],
        "win_rate": best_row["win_rate"],
        "num_games": best_row["num_games"],
        "reason": f"Highest avg_score_diff ({best_row['avg_score_diff']}) across training opponents",
    }

    best_c_path = os.path.join(OUTPUT_DIR, "best_c.json")
    with open(best_c_path, "w") as f:
        json.dump(best_c_dict, f, indent=2)
    print(f"✓ Best c: {best_c_path}")

    # Print summary table
    print(f"\n{'c':>6}  {'Wins':>5}  {'WinRate':>8}  {'Avg Diff':>10}  {'Avg Agent':>10}  {'Avg Opp':>9}")
    print("─" * 65)
    for row in summary_rows:
        marker = " ★" if row["c"] == best_c else ""
        print(f"{row['c']:>6.2f}  {int(row['win_rate']*row['num_games']):>5}  "
              f"{row['win_rate']:>7.1%}  {row['avg_score_diff']:>10.2f}  "
              f"{row['avg_agent_score']:>10.2f}  {row['avg_opponent_score']:>9.2f}{marker}")
    print("─" * 65)
    print(f"\n★ BEST: c = {best_c:.2f}  (score_diff = {best_row['avg_score_diff']:.2f})")
    print(f"\nNext step: python3 tune_c_bandit.py")


if __name__ == "__main__":
    main()
