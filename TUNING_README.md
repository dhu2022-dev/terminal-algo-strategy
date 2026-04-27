#!/usr/bin/env python3
"""
TUNING INFRASTRUCTURE GUIDE

This directory contains an automated parameter tuning pipeline for discovering
optimal aggression values (c) for the C1 Terminal rule-based bot.

## Quick Start

    # 1. Grid search over 11 c values × 3 training opponents
    python3 tune_c_grid.py

    # 2. Bandit-based adaptive tuning (50 episodes)
    python3 tune_c_bandit.py --episodes 50

    # 3. Evaluate on held-out test opponents
    python3 test_selected_c.py --matches 10

    # 4. Generate presentation plots
    python3 plot_tuning_results.py

    # 5. Write experiment summary
    python3 experiment_summary.py

    # View the summary
    open experiment_summary.md

## File Overview

├── experiment_config.json
│   └─ Configuration: c values, opponent set, metrics
│
├── tune_c_grid.py
│   └─ Grid search: exhaustive evaluation of c values × opponents
│       → Results: results/tuning/grid/{tuning_results.csv, best_c.json, tuning_summary.csv}
│
├── tune_c_bandit.py
│   └─ Bandit algorithm: ε-greedy multi-armed bandit for adaptive tuning
│       → Results: results/tuning/bandit/{bandit_results.csv, best_c_bandit.json, bandit_summary.csv}
│
├── test_selected_c.py
│   └─ Generalization: test tuned c on held-out opponents
│       → Results: results/testing/{test_results.csv, test_summary.csv, test_comparison.json}
│
├── plot_tuning_results.py
│   └─ Visualization: generate 7 presentation-ready plots
│       → Results: results/figures/{*.png}
│
├── experiment_summary.py
│   └─ Documentation: comprehensive markdown report
│       → Results: experiment_summary.md
│
└── opponents/
    ├── starter_baseline/        # Reference (C1 official starter)
    ├── defensive_opponent/      # c = 0.1 (defensive)
    ├── balanced_opponent/       # c = 0.5 (balanced)
    └── aggressive_opponent/     # c = 0.85 (aggressive)


## Configuration (experiment_config.json)

Controls what gets tuned:

```json
{
  "c_values": [0.0, 0.1, 0.2, ..., 1.0],     # 11 aggression levels
  "train_opponents": ["starter_baseline", "defensive_opponent", "aggressive_opponent"],
  "test_opponents": ["balanced_opponent"],     # Held-out for testing
  "games_per_c_per_opponent": 3,              # Grid search repetitions
  "metrics": ["score_diff", "win_rate"],       # Evaluation metrics
}
```

Change these to:
- Test different c values: modify `c_values`
- Add more training opponents: add to `opponents/` and update `train_opponents`
- Change test opponent: update `test_opponents`


## Tuning Algorithms

### Grid Search (tune_c_grid.py)
- Evaluates every c value against every training opponent
- Simple, exhaustive, shows full performance landscape
- Best when parameter space is small
- Output: complete score matrix, heatmap-ready data

### Bandit (tune_c_bandit.py)
- Multi-armed bandit with ε-greedy exploration/exploitation
- Learns Q-values incrementally: Q[c] ← Q[c] + (reward - Q[c]) / n_pulls
- Epsilon decays to shift from exploration → exploitation
- Best when you want to reduce total episodes while finding good c
- Output: learning curves, final Q-value estimates

### Usage Patterns

**Pattern 1: Quick exploration**
```bash
python3 tune_c_grid.py          # Takes ~1 hour
python3 test_selected_c.py      # Takes ~10 mins
python3 plot_tuning_results.py  # Takes <1 min
```

**Pattern 2: Conservative tuning**
```bash
python3 tune_c_grid.py --games 5          # More exhaustive
python3 test_selected_c.py --matches 15   # More validation
```

**Pattern 3: Comparative study**
```bash
python3 tune_c_grid.py
python3 tune_c_bandit.py --episodes 100   # Long bandit run
python3 test_selected_c.py
# Compare grid vs bandit in results/testing/test_summary.csv
```


## Results Directory Structure

results/
├── tuning/
│   ├── grid/
│   │   ├── tuning_results.csv        # Per-match: c, opponent, score_diff, win, replay_path
│   │   ├── tuning_summary.csv        # Aggregated by c: win_rate, avg_score_diff
│   │   ├── best_c.json              # Selected c value + metrics
│   │   └── replays/                 # All match replays organized by c
│   │
│   └── bandit/
│       ├── bandit_results.csv        # Per-episode: c, opponent, score_diff, q_value, epsilon
│       ├── bandit_summary.csv        # Aggregated by c: pulls, final_q_value
│       ├── best_c_bandit.json       # Selected c + metrics
│       └── replays/                 # All match replays by episode
│
├── testing/
│   ├── test_results.csv             # Per-match on test opponents
│   ├── test_summary.csv             # Aggregated by c on test opponents
│   ├── test_comparison.json         # Best c vs baselines
│   └── replays/                     # Test match replays
│
└── figures/
    ├── training_heatmap_score_diff.png      # Heatmap: c × opponent → score_diff
    ├── training_winrate_by_c.png            # Bar: win rate by c
    ├── training_score_diff_by_c.png         # Bar: avg score diff by c
    ├── bandit_learning_curve.png            # Line: cumulative reward over episodes
    ├── bandit_q_values_by_c.png             # Bar: final Q-values
    ├── test_comparison.png                  # Bar: test performance (grid vs bandit vs baselines)
    └── generalization_heatmap.png           # Heatmap: c × test_opponent → win_rate


## Output Formats

### CSV Files

**tuning_results.csv (grid search, per-match)**
```
c,opponent,run_id,agent_score,opponent_score,score_diff,win,turns,replay_path
0.2,starter_baseline,1,50,40,10,1,100,results/tuning/grid/replays/c_0.20/starter_baseline_1.replay
...
```

**tuning_summary.csv (grid search, aggregated)**
```
c,num_games,win_rate,avg_score_diff,avg_turns
0.0,9,0.333,5.1,95.2
0.1,9,0.444,6.3,102.1
...
```

**bandit_results.csv (per-episode)**
```
episode,c,opponent,agent_score,opponent_score,score_diff,win,turns,q_value,epsilon,replay_path
1,0.5,defensive_opponent,45,35,10,1,100,5.0,0.300,results/tuning/bandit/replays/ep_0001/match.replay
...
```

**test_results.csv (held-out test)**
```
c,c_label,opponent,test_id,agent_score,opponent_score,score_diff,win,turns,replay_path
0.1,defensive,balanced_opponent,1,42,50,-8,0,105,results/testing/replays/c_0.10_01/match.replay
...
```

### JSON Files

**best_c.json (grid search selection)**
```json
{
  "c_best": 0.7,
  "win_rate": 0.667,
  "avg_score_diff": 8.5,
  "num_games": 9,
  "reason": "Highest avg_score_diff across training opponents"
}
```

**best_c_bandit.json (bandit selection)**
```json
{
  "c_best": 0.65,
  "final_q_value": 7.234,
  "win_rate": 0.6,
  "avg_score_diff": 7.2,
  "pulls": 50,
  "reason": "Highest learned Q-value after 50 episodes"
}
```

**test_comparison.json (testing summary)**
```json
{
  "test_opponents": ["balanced_opponent"],
  "matches_per_c": 10,
  "best_c_on_test": {
    "c": 0.65,
    "c_label": "bandit",
    "win_rate": 0.7,
    "avg_score_diff": 8.5
  },
  "summary": [...]
}
```


## Interpreting Results

### Good Signs
✓ Best c found is NOT an extreme (not exactly 0.0 or 1.0)
✓ Win rate improves as c is tuned (not random)
✓ Test set performance ≥ training performance (no overfitting)
✓ Grid and bandit converge to similar c values (robustness)

### Red Flags
✗ Best c is extreme (0.0 or 1.0) → parameter space too limited
✗ Test performance much worse than training → possible overfitting
✗ Grid and bandit disagree significantly → need more training
✗ High variance in replays → need more runs per (c, opponent) combo


## Customization

### Change parameter range
Edit experiment_config.json:
```json
"c_values": [0.0, 0.05, 0.1, 0.15, ..., 1.0]  # Finer granularity
```

### Add more training opponents
1. Create `opponents/my_opponent/` with run.sh and bot code
2. Add to experiment_config.json:
   ```json
   "train_opponents": ["starter_baseline", "defensive_opponent", "my_opponent"]
   ```

### Run longer
```bash
python3 tune_c_grid.py --config experiment_config.json  # Uses config games_per_c_per_opponent
python3 tune_c_bandit.py --episodes 200 --epsilon 0.4
python3 test_selected_c.py --matches 20
```

### Change metrics
Edit the aggregation functions in tune_c_grid.py, tune_c_bandit.py to use:
- `score_diff` (default): absolute score advantage
- `win_rate`: fraction of wins
- `turns`: game length
- `resource_efficiency`: points_per_resource


## Troubleshooting

### Matches hang or timeout
- Increase timeout in scripts (default 300s)
- Check that engine.jar is runnable: `java -jar engine.jar version`

### No replays found
- Verify replays/ directory exists
- Check engine output: `java -jar engine.jar work player1/run.sh player2/run.sh`

### CSV parsing errors
- Ensure replays have valid JSON with endStats object
- Check parse_replay() function handles your replay format

### Matplotlib import error
- Install matplotlib: `pip install matplotlib pandas numpy`


## Tips for Presentation

### Best visualizations for class
1. **training_heatmap_score_diff.png** — Shows parameter landscape clearly
2. **test_comparison.png** — Demonstrates tuned c beats baselines
3. **bandit_learning_curve.png** — Shows adaptive exploration over time

### Key talking points
- "This is parameter tuning, not agent training"
- "Grid search exhaustively evaluates the space; bandit learns efficiently"
- "Test set validates that tuned c generalizes to unseen opponents"
- "Diversity of training opponents improves robustness"


## Next Steps

After running the full pipeline:

1. **Review experiment_summary.md** for comprehensive report
2. **Check results/figures/** for presentation-ready plots
3. **Examine test_summary.csv** to see if tuned c beats baselines
4. **Run analysis:** How much does tuning help vs fixed c?
5. **Consider extensions:** Multi-parameter tuning? More opponents? Different metrics?
"""

if __name__ == "__main__":
    print(__doc__)
