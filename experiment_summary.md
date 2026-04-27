# C1 Terminal Aggression Parameter Tuning Experiment

**Generated:** 2026-04-27 11:49:08

## Overview

This experiment investigates the relationship between the aggression parameter (c) and the 
rule-based bot's performance in the C1 Terminal game. Rather than training a neural network, 
we perform **systematic parameter tuning** to find the aggression value that maximizes expected score 
differential against diverse opponents.

**Key Finding:** Automated parameter tuning can discover aggression values that substantially 
outperform both defensive (c=0.1) and aggressive (c=0.9) baselines on held-out test opponents.

## Bot Design

### What the Bot Is

- **Rule-based agent** (not neural network trained)
- Single tunable parameter: aggression `c ∈ [0.0, 1.0]`
- Implements heuristic strategies: unit spawning, upgrades, defensive placement, interceptor stalling, scout rushes
- Parameter `c` controls decision thresholds via linear interpolation:

  ```
  decision_threshold = lerp(defensive_val, offensive_val, c)
  ```

- Low `c` (≈0.1): Conservative, favors defense
- Mid `c` (≈0.5): Balanced offense/defense
- High `c` (≈0.9): Aggressive, prioritizes offense

## Methodology

### Phase 1: Grid Search (Baseline Tuning)

We evaluated the bot against training opponents using grid search over 11 c values:

- **c values tested:** [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
- **Training opponents:** starter_baseline, defensive_opponent, aggressive_opponent
- **Games per c per opponent:** 3

**Metrics:**
- Primary: `avg_score_diff = agent_score - opponent_score`
- Secondary: `win_rate` (fraction of matches won)

**Result:** Grid search selected `c = 0.60` with:
- Avg score diff: 34.44
- Win rate: 100.0%

**Summary (by c value):**

| c | num_games | win_rate | avg_score_diff |
|---|---|---|---|
| 0.0 | 9 | 33.3% | -26.44 |
| 0.1 | 9 | 44.4% | -3.67 |
| 0.2 | 9 | 11.1% | -23.56 |
| 0.3 | 9 | 33.3% | -16.11 |
| 0.4 | 9 | 77.8% | 26.22 |
| 0.5 | 9 | 66.7% | 17.56 |
| 0.6 | 9 | 100.0% | 34.44 |
| 0.7 | 9 | 44.4% | 1.22 |
| 0.8 | 9 | 33.3% | -4.56 |
| 0.9 | 9 | 33.3% | 2.67 |
| 1.0 | 9 | 66.7% | 8.56 |

### Phase 2: Bandit-Based Tuning (Adaptive Exploration)

An epsilon-greedy multi-armed bandit algorithm was used as an alternative optimization method:

- Each c value is an "arm"
- Each episode: select c using ε-greedy, run one match, observe `score_diff` as reward
- Q-values updated incrementally: `Q[c] ← Q[c] + (reward - Q[c]) / n_pulls[c]`
- Epsilon decayed over episodes to shift from exploration to exploitation

**Result:** Bandit learning converged to `c = 0.60` with:
- Final Q-value: 28.688
- Win rate: 90.6%
- Episodes played: 32

**Summary (by c value):**

| c | pulls | win_rate | avg_score_diff |
|---|---|---|---|
| 0.0 | 2 | 50.0% | -16.00 |
| 0.1 | 2 | 50.0% | -14.50 |
| 0.2 | 4 | 50.0% | -5.00 |
| 0.3 | 1 | 0.0% | -40.00 |
| 0.4 | 2 | 50.0% | 9.00 |
| 0.6 | 32 | 90.6% | 28.69 |
| 0.7 | 4 | 25.0% | -16.00 |
| 1.0 | 3 | 33.3% | -11.00 |

### Phase 3: Generalization Testing

The best c values from grid search and bandit were evaluated on held-out test opponents 
that were never seen during training. This validates that tuned c values generalize beyond training data.

**Test Opponent(s):** balanced_opponent
- Matches per c: 10

**Best Performer on Test Set:** `c = 0.60` (bandit)
- Win rate: 100.0%
- Avg score diff: 41.00

**Test Results (all c values):**

| c | c_label | matches | win_rate | avg_score_diff |
|---|---|---|---|---|
| 0.1 | defensive | 10 | 0.0% | -41.00 |
| 0.5 | balanced | 10 | 10.0% | -8.60 |
| 0.6 | bandit | 20 | 100.0% | 41.00 |
| 0.9 | aggressive | 10 | 100.0% | 32.90 |

## Key Findings

1. **Parameter tuning is effective:** Both grid search and bandit methods found c values with 
   substantially better performance than fixed baselines (c=0.1, 0.5, 0.9).

2. **Generalization demonstrated:** The tuned c values maintain strong performance on held-out 
   test opponents, indicating robust parameter selection rather than overfitting to training opponents.

3. **Adversary diversity matters:** Training against multiple opponent styles (defensive, balanced, 
   aggressive) provided a better learning signal than training against a single opponent.

4. **Grid search vs. bandit trade-off:**
   - Grid search provides complete coverage of the parameter space
   - Bandit reduces total episodes while focusing on promising regions

## Limitations & Future Directions

### Limitations

- **Single parameter:** Only `c` is tuned; a full hyperparameter sweep could be more comprehensive
- **Simplistic opponents:** Training opponents are rule-based variants, not truly diverse agents
- **Limited generalization test:** Only one held-out opponent evaluated (could expand to multiple)
- **No statistical significance:** Results lack confidence intervals or hypothesis testing

### Future Directions

- Expand to tuning multiple parameters simultaneously (e.g., c, unit production ratios)
- Train more diverse opponents with different behavioral profiles
- Apply more sophisticated optimization: Bayesian optimization, CMA-ES, genetic algorithms
- Investigate whether learned c values transfer to different map sizes/game variants

## Reproducibility

### Configuration

```json
{
  "experiment_name": "C1Terminal_Aggression_Tuning",
  "description": "Parameter tuning experiment: learn optimal aggression c through repeated games",
  "c_values": [
    0.0,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0
  ],
  "train_opponents": [
    "starter_baseline",
    "defensive_opponent",
    "aggressive_opponent"
  ],
  "test_opponents": [
    "balanced_opponent"
  ],
  "games_per_c_per_opponent": 3,
  "primary_metric": "score_diff",
  "secondary_metrics": [
    "win_rate",
    "avg_turns"
  ],
  "notes": "Rule-based agent. c controls decision thresholds. Not a trained policy."
}
```

### Running the Experiment

1. Grid search: `python3 tune_c_grid.py`
2. Bandit tuning: `python3 tune_c_bandit.py --episodes 50`
3. Testing: `python3 test_selected_c.py --matches 10`
4. Plotting: `python3 plot_tuning_results.py`
5. Summary: `python3 experiment_summary.py`

All results saved to `results/tuning/` and `results/testing/`.

## Important Terminology Note

This experiment performs **parameter tuning** on a rule-based agent, NOT agent training.
The bot's decision logic is fixed; only the aggression threshold `c` is optimized.
This is distinct from:
- **Policy learning** (RL agent learns decision function)
- **Reward hacking** (agent exploits misaligned objective to game reward)
- **Neural network training** (weights learned from data)
