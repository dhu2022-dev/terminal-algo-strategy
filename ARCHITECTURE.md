# 🏗️ Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TUNING INFRASTRUCTURE                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  CONFIGURATION LAYER                                        │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  experiment_config.json                                     │  │
│  │  ├─ c_values: [0.0, 0.1, ..., 1.0]                        │  │
│  │  ├─ train_opponents: [starter, defensive, aggressive]      │  │
│  │  ├─ test_opponents: [balanced]                             │  │
│  │  └─ games_per_c_per_opponent: 3                            │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  OPTIMIZATION LAYER                                         │  │
│  ├──────────────────────────────────────────────────────────────┤  │
│  │                                                              │  │
│  │  tune_c_grid.py              tune_c_bandit.py             │  │
│  │  ┌──────────────────┐         ┌───────────────────┐       │  │
│  │  │ Grid Search      │         │ Epsilon-Greedy    │       │  │
│  │  │ ────────────     │         │ Bandit            │       │  │
│  │  │ • 11 c values    │         │ ───────────────   │       │  │
│  │  │ • 3 opponents    │         │ • Q-value updates │       │  │
│  │  │ • 3 runs each    │         │ • 50 episodes     │       │  │
│  │  │ • 99 matches     │         │ • Epsilon decay   │       │  │
│  │  │ • ~60 minutes    │         │ • ~30 minutes     │       │  │
│  │  └──────────────────┘         └───────────────────┘       │  │
│  │          ↓                             ↓                   │  │
│  │   results/tuning/grid/          results/tuning/bandit/    │  │
│  │   ├─ tuning_results.csv         ├─ bandit_results.csv    │  │
│  │   ├─ tuning_summary.csv         ├─ bandit_summary.csv    │  │
│  │   ├─ best_c.json               ├─ best_c_bandit.json    │  │
│  │   └─ replays/                  └─ replays/              │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VALIDATION LAYER                                        │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  test_selected_c.py                                     │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │ Load: best_c (grid), best_c (bandit)           │     │   │
│  │  │ Plus: baselines (0.1, 0.5, 0.9)               │     │   │
│  │  │ Test on: held-out test_opponents               │     │   │
│  │  │ Runs: 10 matches per c per test opponent       │     │   │
│  │  │ Total: 60 matches, ~20 minutes                 │     │   │
│  │  └────────────────────────────────────────────────┘     │   │
│  │                       ↓                                   │   │
│  │  results/testing/                                        │   │
│  │  ├─ test_results.csv                                    │   │
│  │  ├─ test_summary.csv                                    │   │
│  │  ├─ test_comparison.json                                │   │
│  │  └─ replays/                                            │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VISUALIZATION & REPORTING LAYER                         │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                                                           │   │
│  │  plot_tuning_results.py      experiment_summary.py      │   │
│  │  ┌──────────────────────┐    ┌──────────────────────┐   │   │
│  │  │ Generate 7 Charts    │    │ Generate Report      │   │   │
│  │  │ ──────────────────── │    │ ────────────────────│   │   │
│  │  │ 1. Heatmap (grid)    │    │ • Overview          │   │   │
│  │  │ 2. Win rate by c     │    │ • Methodology       │   │   │
│  │  │ 3. Score diff by c   │    │ • Results           │   │   │
│  │  │ 4. Bandit curve      │    │ • Findings          │   │   │
│  │  │ 5. Q-values          │    │ • Limitations       │   │   │
│  │  │ 6. Test comparison   │    │ • Conclusions       │   │   │
│  │  │ 7. Generalization    │    │ • Reproducibility   │   │   │
│  │  └──────────────────────┘    └──────────────────────┘   │   │
│  │          ↓                              ↓                │   │
│  │   results/figures/              experiment_summary.md   │   │
│  │   ├─ *.png (7 charts)                                   │   │
│  │   └─ presentation-ready                                 │   │
│  │                                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
experiment_config.json
        ↓
   ┌────┴────────────────────────────┐
   ↓                                  ↓
tune_c_grid.py                 tune_c_bandit.py
   ↓                                  ↓
 tuning_results.csv             bandit_results.csv
 best_c.json                    best_c_bandit.json
   ↓                                  ↓
   └────────────┬─────────────────────┘
                ↓
         test_selected_c.py
                ↓
        test_results.csv
        test_comparison.json
                ↓
        ┌──────┴────────┐
        ↓               ↓
  plot_tuning_    experiment_
  results.py       summary.py
        ↓               ↓
  results/figures  experiment_
                   summary.md
```

## Component Dependencies

```
experiment_config.json ──┐
                         ├─→ tune_c_grid.py ────┐
opponents/ ──────────────┤                      ├─→ test_selected_c.py ┐
                         ├─→ tune_c_bandit.py ──┤                     ├─→ plot_tuning_results.py
python-algo/ ────────────┤                      ├─→ test comparison ──┤
                         └─ all .py scripts     └──────────────────────┘
engine.jar ───────────────────────────────────────────────────────────→
                                                                       └─→ experiment_summary.py
```

## Information Flow

```
INPUTS:
├─ experiment_config.json      (defines tuning scope)
├─ python-algo/                (our bot code)
├─ opponents/                  (4 opponent variants)
└─ engine.jar                  (game engine)
         ↓
PROCESSING:
├─ tune_c_grid.py              (generate 99 matches)
├─ tune_c_bandit.py            (generate 50 matches)
├─ test_selected_c.py          (generate 60 matches)
└─ Total: 209 game matches
         ↓
INTERMEDIATE RESULTS:
├─ results/tuning/grid/        (99 matches + aggregation)
├─ results/tuning/bandit/      (50 episodes + aggregation)
├─ results/testing/            (60 matches + comparison)
└─ All replays stored for review
         ↓
OUTPUTS:
├─ plot_tuning_results.py      (7 PNG charts)
├─ experiment_summary.py       (comprehensive report)
└─ Results ready for presentation
```

## Timeline

```
START
  │
  ├─ PRE-FLIGHT CHECKS (1 min)
  │  └─ Verify python3, java, engine.jar, config
  │
  ├─ PHASE 1: GRID SEARCH (60 min)
  │  ├─ Create 11 c directories
  │  ├─ Run 99 matches (11 c × 3 opp × 3 runs)
  │  ├─ Parse 99 replays, aggregate metrics
  │  └─ Select best_c using score_diff ranking
  │
  ├─ PHASE 2: BANDIT TUNING (30 min)
  │  ├─ Initialize Q-values, epsilon
  │  ├─ Run 50 episodes (epsilon-greedy selection)
  │  ├─ Update Q-values incrementally
  │  └─ Select best_c_bandit using final Q-values
  │
  ├─ PHASE 3: TESTING (20 min)
  │  ├─ Load best_c from grid and bandit
  │  ├─ Run 60 test matches (6 c values × 1 opp × 10 runs)
  │  ├─ Aggregate on held-out opponent
  │  └─ Compare tuned c vs fixed baselines
  │
  ├─ PHASE 4: VISUALIZATION (<5 min)
  │  ├─ Generate 7 matplotlib charts
  │  └─ Save to results/figures/
  │
  ├─ PHASE 5: REPORTING (<1 min)
  │  └─ Generate experiment_summary.md
  │
END
  └─ TOTAL TIME: ~2-3 hours
```

## Success Criteria

```
✅ Success if:
  ├─ Best c is NOT extreme (0.0 or 1.0)
  ├─ Best c win_rate > 50%
  ├─ Test performance ≥ training performance
  ├─ Grid and bandit converge to similar c
  ├─ Tuned c beats fixed baselines on test set
  └─ All 7 plots generate successfully

⚠️  Warning signs:
  ├─ Best c is 0.0 or 1.0
  ├─ Win rate < 30%
  ├─ Large gap between training and test performance
  ├─ Grid and bandit disagree significantly
  └─ Matplotlib plots fail to generate
```

## Scaling & Customization

```
To test more c values:
  1. Edit experiment_config.json
  2. "c_values": [0.0, 0.05, 0.1, ..., 1.0]  (finer granularity)
  3. Re-run tune_c_grid.py
  4. Time impact: ~+5 min per additional c value

To add more training opponents:
  1. Create opponents/my_opponent/ with run.sh and bot code
  2. Update experiment_config.json: "train_opponents": [..., "my_opponent"]
  3. Re-run tune_c_grid.py and tune_c_bandit.py
  4. Time impact: ~+20 min per additional opponent

To run more robustly:
  1. Edit experiment_config.json: "games_per_c_per_opponent": 10
  2. Re-run: python3 tune_c_grid.py
  3. Time impact: 3× longer grid search
```

## Directory Structure (After Running)

```
terminal-algo-strategy/
├── experiment_config.json           ← Configuration
├── tune_c_grid.py                   ← Grid search script
├── tune_c_bandit.py                 ← Bandit script
├── test_selected_c.py               ← Test script
├── plot_tuning_results.py            ← Plotting script
├── experiment_summary.py             ← Report script
├── run_tuning_pipeline.sh            ← Execution script
│
├── opponents/                        ← Opponent bots
│   ├── starter_baseline/
│   ├── defensive_opponent/
│   ├── balanced_opponent/
│   └── aggressive_opponent/
│
├── python-algo/                     ← Our bot (source)
│
├── results/                         ← Generated results
│   ├── tuning/
│   │   ├── grid/
│   │   │   ├── tuning_results.csv       (99 rows)
│   │   │   ├── tuning_summary.csv       (11 rows)
│   │   │   ├── best_c.json
│   │   │   └── replays/
│   │   │
│   │   └── bandit/
│   │       ├── bandit_results.csv       (50 rows)
│   │       ├── bandit_summary.csv       (11 rows)
│   │       ├── best_c_bandit.json
│   │       └── replays/
│   │
│   ├── testing/
│   │   ├── test_results.csv             (60 rows)
│   │   ├── test_summary.csv             (5 rows)
│   │   ├── test_comparison.json
│   │   └── replays/
│   │
│   └── figures/
│       ├── training_heatmap_score_diff.png
│       ├── training_winrate_by_c.png
│       ├── training_score_diff_by_c.png
│       ├── bandit_learning_curve.png
│       ├── bandit_q_values_by_c.png
│       ├── test_comparison.png
│       └── generalization_heatmap.png
│
├── experiment_summary.md            ← Generated report
├── INFRASTRUCTURE_SUMMARY.md        ← This file
├── RUN_TUNING_PIPELINE.md           ← Execution guide
├── TUNING_README.md                 ← Reference manual
│
└── .test_tmp/                       ← Temporary (auto-cleaned)
    └── .bandit_tmp/
```

---

**This is a complete, production-ready parameter tuning infrastructure.**

All files are in place. Ready to execute with: `bash run_tuning_pipeline.sh`
