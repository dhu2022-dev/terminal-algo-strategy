#!/usr/bin/env python3
"""
tune_c_bandit.py — Epsilon-greedy multi-armed bandit for parameter tuning.

This script uses bandit-style exploration/exploitation to learn good values of c.

Each c value is an "arm". We run episodes where:
1. Choose a c using epsilon-greedy (explore vs exploit)
2. Pick a random training opponent
3. Run one match
4. Observe reward = agent_score - opponent_score
5. Update Q[c] incrementally

Outputs:
- results/tuning/bandit/bandit_results.csv (per-episode)
- results/tuning/bandit/bandit_summary.csv (aggregated by c)
- results/tuning/bandit/best_c_bandit.json (selected c)

Usage:
    python3 tune_c_bandit.py [--episodes 100] [--epsilon 0.3]
"""

import argparse
import csv
import json
import os
import random
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
OUTPUT_DIR = os.path.join(ROOT, "results", "tuning", "bandit")
REPLAY_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "replays")


def load_config():
    """Load experiment configuration."""
    with open(CONFIG, "r") as f:
        return json.load(f)


def make_agent_dir(c_value: float, episode: int) -> str:
    """Create temp agent directory."""
    name = f"bandit_c{c_value:.2f}_ep{episode}"
    dest = os.path.join(ROOT, ".bandit_tmp", name)
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


def run_episode(c_value: float, opponent_name: str, episode: int) -> dict | None:
    """Run one bandit episode."""
    agent_dir = make_agent_dir(c_value, episode)
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
        dest_folder = os.path.join(REPLAY_OUTPUT_DIR, f"ep_{episode:04d}")
        os.makedirs(dest_folder, exist_ok=True)
        dest_path = os.path.join(dest_folder, "match.replay")
        shutil.move(replay, dest_path)

        return {
            "c": c_value,
            "opponent": opponent_name,
            "episode": episode,
            "agent_score": metrics["agent_score"],
            "opponent_score": metrics["opponent_score"],
            "score_diff": metrics["agent_score"] - metrics["opponent_score"],
            "win": metrics["win"],
            "turns": metrics["turns"],
            "replay_path": dest_path,
        }

    except Exception as e:
        return None


def epsilon_greedy(c_values: list, q_values: dict, epsilon: float) -> float:
    """Choose c using epsilon-greedy."""
    if random.random() < epsilon:
        return random.choice(c_values)
    else:
        return max(c_values, key=lambda c: q_values.get(c, 0))


def main():
    parser = argparse.ArgumentParser(description="Bandit-based c tuning")
    parser.add_argument("--episodes", type=int, default=50,
                        help="Number of episodes (default 50)")
    parser.add_argument("--epsilon", type=float, default=0.3,
                        help="Exploration rate (default 0.3)")
    parser.add_argument("--decay", type=float, default=0.995,
                        help="Epsilon decay per episode (default 0.995)")
    args = parser.parse_args()

    print("═" * 80)
    print("BANDIT-BASED PARAMETER TUNING")
    print("═" * 80)

    config = load_config()
    c_values = config["c_values"]
    train_opponents = config["train_opponents"]

    print(f"\nConfiguration:")
    print(f"  c values: {c_values}")
    print(f"  opponents: {train_opponents}")
    print(f"  episodes: {args.episodes}")
    print(f"  epsilon (initial): {args.epsilon}")
    print(f"  epsilon decay: {args.decay}\n")

    # Pre-flight checks
    if not os.path.isfile(ENGINE):
        print("ERROR: engine.jar not found")
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPLAY_OUTPUT_DIR, exist_ok=True)

    # Initialize bandit state
    q_values = {c: 0.0 for c in c_values}  # estimated value
    n_pulls = {c: 0 for c in c_values}  # visit count
    epsilon = args.epsilon

    results = []

    print(f"Running {args.episodes} episodes...\n")

    for episode in range(1, args.episodes + 1):
        # Select c
        c_selected = epsilon_greedy(c_values, q_values, epsilon)

        # Select opponent
        opponent_selected = random.choice(train_opponents)

        # Run episode
        print(f"[Episode {episode:3d}] c={c_selected:.2f}, opp={opponent_selected:15s}, epsilon={epsilon:.3f}...", 
              end=" ", flush=True)

        episode_result = run_episode(c_selected, opponent_selected, episode)

        if episode_result:
            reward = episode_result["score_diff"]
            n_pulls[c_selected] += 1
            # Incremental average update: Q[c] += (reward - Q[c]) / n
            q_values[c_selected] += (reward - q_values[c_selected]) / n_pulls[c_selected]
            episode_result["q_value"] = round(q_values[c_selected], 3)
            episode_result["epsilon"] = round(epsilon, 4)
            results.append(episode_result)
            print(f"reward={reward:6.1f}, Q[c]={q_values[c_selected]:7.2f}")
        else:
            print(f"FAILED")

        # Decay epsilon
        epsilon *= args.decay

    # Cleanup
    tmp_dir = os.path.join(ROOT, ".bandit_tmp")
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)

    # Write per-episode CSV
    if not results:
        print("\nERROR: No results collected")
        sys.exit(1)

    csv_path = os.path.join(OUTPUT_DIR, "bandit_results.csv")
    fieldnames = ["episode", "c", "opponent", "agent_score", "opponent_score",
                  "score_diff", "win", "turns", "q_value", "epsilon", "replay_path"]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\n✓ Per-episode results: {csv_path}")

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
        final_q = q_values[c]

        summary_rows.append({
            "c": c,
            "pulls": n,
            "win_rate": round(wins / n, 3),
            "avg_score_diff": round(avg_score_diff, 2),
            "final_q_value": round(final_q, 3),
        })

    summary_csv = os.path.join(OUTPUT_DIR, "bandit_summary.csv")
    with open(summary_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"✓ Summary by c: {summary_csv}")

    # Select best c (highest final Q value)
    best_c = max(c_values, key=lambda c: q_values[c])
    best_row = next(r for r in summary_rows if r["c"] == best_c)

    best_c_bandit = {
        "c_best": best_c,
        "final_q_value": best_row["final_q_value"],
        "win_rate": best_row["win_rate"],
        "avg_score_diff": best_row["avg_score_diff"],
        "pulls": best_row["pulls"],
        "reason": f"Highest learned Q-value ({best_row['final_q_value']}) after {args.episodes} episodes",
    }

    best_c_path = os.path.join(OUTPUT_DIR, "best_c_bandit.json")
    with open(best_c_path, "w") as f:
        json.dump(best_c_bandit, f, indent=2)
    print(f"✓ Best c (bandit): {best_c_path}")

    # Print summary
    print(f"\n{'c':>6}  {'Pulls':>5}  {'WinRate':>8}  {'Avg Diff':>10}  {'Final Q':>10}")
    print("─" * 50)
    for row in summary_rows:
        marker = " ★" if row["c"] == best_c else ""
        print(f"{row['c']:>6.2f}  {row['pulls']:>5}  {row['win_rate']:>7.1%}  "
              f"{row['avg_score_diff']:>10.2f}  {row['final_q_value']:>10.3f}{marker}")
    print("─" * 50)
    print(f"\n★ BEST: c = {best_c:.2f}  (Q = {q_values[best_c]:.3f})")
    print(f"\nNext step: python3 test_selected_c.py")


if __name__ == "__main__":
    main()
