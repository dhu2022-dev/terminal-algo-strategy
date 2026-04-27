#!/usr/bin/env python3
"""
test_selected_c.py — Evaluate the tuned c values on held-out test opponents.

This script:
1. Loads best_c from both grid search and bandit outputs
2. Tests each best_c against test opponents
3. Compares against baseline c values (0.1, 0.5, 0.9)
4. Computes test metrics (win_rate, avg_score_diff)

Outputs:
- results/testing/test_results.csv (per-match)
- results/testing/test_summary.csv (aggregated by c)
- results/testing/test_comparison.json (best_c vs baselines)

Usage:
    python3 test_selected_c.py [--matches 10]
"""

import argparse
import csv
import json
import os
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
GRID_BEST_C = os.path.join(ROOT, "results", "tuning", "grid", "best_c.json")
BANDIT_BEST_C = os.path.join(ROOT, "results", "tuning", "bandit", "best_c_bandit.json")
OUTPUT_DIR = os.path.join(ROOT, "results", "testing")
REPLAY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "replays")


def load_config():
    """Load experiment configuration."""
    with open(CONFIG, "r") as f:
        return json.load(f)


def load_best_c_values() -> dict:
    """Load best c from grid and bandit results."""
    best_c = {}

    if os.path.isfile(GRID_BEST_C):
        with open(GRID_BEST_C, "r") as f:
            data = json.load(f)
            best_c["grid"] = data["c_best"]
            print(f"✓ Loaded grid search best_c: {data['c_best']:.2f}")
    else:
        print(f"⚠ Grid search results not found ({GRID_BEST_C})")

    if os.path.isfile(BANDIT_BEST_C):
        with open(BANDIT_BEST_C, "r") as f:
            data = json.load(f)
            best_c["bandit"] = data["c_best"]
            print(f"✓ Loaded bandit best_c: {data['c_best']:.2f}")
    else:
        print(f"⚠ Bandit results not found ({BANDIT_BEST_C})")

    # Add baselines
    best_c["defensive"] = 0.1
    best_c["balanced"] = 0.5
    best_c["aggressive"] = 0.9

    return best_c


def make_agent_dir(c_value: float, test_id: int) -> str:
    """Create temp agent directory."""
    name = f"test_c{c_value:.2f}_t{test_id}"
    dest = os.path.join(ROOT, ".test_tmp", name)
    os.makedirs(dest, exist_ok=True)

    for dirname in ("gamelib", "strategies"):
        src = os.path.join(ALGO_SRC, dirname)
        dst = os.path.join(dest, dirname)
        if os.path.exists(dst):
            os.remove(dst)
        if os.path.isdir(src):
            os.symlink(src, dst)

    for fname in ("algo_strategy.py", "algo.json"):
        src = os.path.join(ALGO_SRC, fname)
        dst = os.path.join(dest, fname)
        shutil.copy2(src, dst)

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


def find_latest_replay():
    """Find most recent replay."""
    import glob
    pattern = os.path.join(ROOT, "replays", "*.replay")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def parse_replay(path: str) -> dict | None:
    """Parse a replay file for metrics."""
    try:
        with open(path, "r") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception:
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
    p1 = end_stats.get("player1", {})
    p2 = end_stats.get("player2", {})

    return {
        "agent_score": p1.get("points_scored", 0),
        "opponent_score": p2.get("points_scored", 0),
        "win": 1 if winner_id == 1 else 0,
        "turns": end_stats.get("turns", 0),
    }


def run_test_match(c_value: float, opponent_name: str, test_id: int) -> dict | None:
    """Run one test match."""
    agent_dir = make_agent_dir(c_value, test_id)
    opponent_path = get_opponent_path(opponent_name)

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
            return None

        replay = find_latest_replay()
        if not replay:
            return None

        metrics = parse_replay(replay)
        if not metrics:
            return None

        # Move replay
        dest_folder = os.path.join(REPLAY_OUTPUT_DIR, f"c_{c_value:.2f}_{test_id:02d}")
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, "match.replay")
        shutil.move(replay, dest_path)

        return {
            "c": c_value,
            "opponent": opponent_name,
            "test_id": test_id,
            "agent_score": metrics["agent_score"],
            "opponent_score": metrics["opponent_score"],
            "score_diff": metrics["agent_score"] - metrics["opponent_score"],
            "win": metrics["win"],
            "turns": metrics["turns"],
            "replay_path": dest_path,
        }

    except Exception as e:
        return None


def main():
    parser = argparse.ArgumentParser(description="Test tuned c on held-out opponents")
    parser.add_argument("--matches", type=int, default=10,
                        help="Matches per c per test opponent (default 10)")
    args = parser.parse_args()

    print("═" * 80)
    print("TESTING TUNED PARAMETERS ON HELD-OUT OPPONENTS")
    print("═" * 80)

    config = load_config()
    test_opponents = config["test_opponents"]

    print(f"\nTest opponents: {test_opponents}")
    print(f"Matches per c: {args.matches}\n")

    # Pre-flight checks
    if not os.path.isfile(ENGINE):
        print("ERROR: engine.jar not found")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPLAY_OUTPUT_DIR, exist_ok=True)

    # Load best c values
    best_c_dict = load_best_c_values()
    
    if not best_c_dict:
        print("ERROR: No best_c values found")
        sys.exit(1)

    print(f"\nTesting {len(best_c_dict)} c values ({len(test_opponents)} test opponents):\n")

    results = []
    tested_cs = []

    for label, c_value in sorted(best_c_dict.items()):
        tested_cs.append(c_value)
        print(f"Testing c={c_value:.2f} ({label:10s})...", flush=True)

        for opponent in test_opponents:
            for match_id in range(1, args.matches + 1):
                print(f"  vs {opponent:15s} match {match_id:2d}/{args.matches}...",
                      end=" ", flush=True)

                match_result = run_test_match(c_value, opponent, match_id)
                if match_result:
                    match_result["c_label"] = label
                    results.append(match_result)
                    print(f"✓ ({match_result['score_diff']:+6.1f})")
                else:
                    print(f"✗")

        print()

    if not results:
        print("ERROR: No test matches completed")
        sys.exit(1)

    # Cleanup
    tmp_dir = os.path.join(ROOT, ".test_tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    # Write per-match CSV
    csv_path = os.path.join(OUTPUT_DIR, "test_results.csv")
    fieldnames = ["c", "c_label", "opponent", "test_id", "agent_score", "opponent_score",
                  "score_diff", "win", "turns", "replay_path"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"✓ Per-match results: {csv_path}\n")

    # Aggregate by c
    by_c = defaultdict(list)
    for row in results:
        by_c[row["c"]].append(row)

    summary_rows = []
    for c in sorted(by_c.keys()):
        rows = by_c[c]
        n = len(rows)
        wins = sum(1 for r in rows if r["win"])
        avg_score_diff = sum(r["score_diff"] for r in rows) / n
        label = rows[0]["c_label"]

        summary_rows.append({
            "c": c,
            "c_label": label,
            "matches": n,
            "win_rate": round(wins / n, 3),
            "avg_score_diff": round(avg_score_diff, 2),
        })

    summary_csv = os.path.join(OUTPUT_DIR, "test_summary.csv")
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"✓ Summary by c: {summary_csv}\n")

    # Build comparison
    comparison = {
        "test_opponents": test_opponents,
        "matches_per_c": args.matches,
        "summary": [
            {
                "c": round(row["c"], 2),
                "c_label": row["c_label"],
                "win_rate": row["win_rate"],
                "avg_score_diff": row["avg_score_diff"],
            }
            for row in summary_rows
        ],
    }

    # Find best performing c on test set
    best_c_test = max(summary_rows, key=lambda r: (r["win_rate"], r["avg_score_diff"]))
    comparison["best_c_on_test"] = {
        "c": round(best_c_test["c"], 2),
        "c_label": best_c_test["c_label"],
        "win_rate": best_c_test["win_rate"],
        "avg_score_diff": best_c_test["avg_score_diff"],
    }

    comp_path = os.path.join(OUTPUT_DIR, "test_comparison.json")
    with open(comp_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"✓ Comparison: {comp_path}\n")

    # Print summary
    print(f"{'c':>6}  {'Label':>10}  {'Win Rate':>10}  {'Avg Diff':>10}")
    print("─" * 50)
    for row in summary_rows:
        marker = " ★" if row["c"] == best_c_test["c"] else ""
        print(f"{row['c']:>6.2f}  {row['c_label']:>10s}  {row['win_rate']:>9.1%}  "
              f"{row['avg_score_diff']:>10.2f}{marker}")
    print("─" * 50)
    print(f"\n★ BEST ON TEST SET: c = {best_c_test['c']:.2f} ({best_c_test['c_label']})")
    print(f"   Win rate: {best_c_test['win_rate']:.1%}")
    print(f"   Avg score diff: {best_c_test['avg_score_diff']:.2f}\n")
    print(f"Next step: python3 plot_tuning_results.py")


if __name__ == "__main__":
    main()
