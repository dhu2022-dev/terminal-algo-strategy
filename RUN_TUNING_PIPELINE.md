# C1 Terminal Tuning Infrastructure — Execution Guide

## Status: READY TO RUN

All infrastructure components have been created:

| Component | File | Purpose | Status |
|-----------|------|---------|--------|
| Configuration | `experiment_config.json` | Define c values, opponents, metrics | ✅ Complete |
| Grid Search | `tune_c_grid.py` | Exhaustive parameter evaluation | ✅ Complete |
| Bandit Tuning | `tune_c_bandit.py` | Adaptive ε-greedy optimization | ✅ Complete |
| Testing | `test_selected_c.py` | Generalization validation | ✅ Complete |
| Plotting | `plot_tuning_results.py` | 7 presentation plots | ✅ Complete |
| Summary | `experiment_summary.py` | Comprehensive documentation | ✅ Complete |
| Documentation | `TUNING_README.md` | Full reference guide | ✅ Complete |

## Execution Pipeline

### Phase 1: Grid Search (Baseline Optimization)

**What it does:** Evaluates every c value against every training opponent.

```bash
python3 tune_c_grid.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
GRID SEARCH TUNING
═══════════════════════════════════════════════════════════════════════════════

Configuration:
  c values: [0.0, 0.1, 0.2, ..., 1.0]
  opponents: [starter_baseline, defensive_opponent, aggressive_opponent]
  games per combo: 3

Running 99 matches (11 c values × 3 opponents × 3 runs)...

[Match   1/99] c=0.00, opp=starter_baseline, run=1... ✓ (score_diff=5.2)
[Match   2/99] c=0.00, opp=starter_baseline, run=2... ✓ (score_diff=3.8)
...

✓ Per-match results: results/tuning/grid/tuning_results.csv
✓ Summary by c: results/tuning/grid/tuning_summary.csv
✓ Best c (grid): results/tuning/grid/best_c.json

c        Win Rate  Avg Diff
─────────────────────────────
0.0      33.3%     2.5
0.1      44.4%     4.2
...
0.7      66.7%     8.5  ★
0.8      55.6%     6.1
1.0      33.3%     1.2

★ BEST: c = 0.70

Next step: python3 tune_c_bandit.py
```

**Time estimate:** ~60 minutes (99 matches × 30-40s per match)

**Output files:**
- `results/tuning/grid/tuning_results.csv` — Per-match details
- `results/tuning/grid/tuning_summary.csv` — Aggregated by c
- `results/tuning/grid/best_c.json` — Selected c value
- `results/tuning/grid/replays/` — All match recordings

---

### Phase 2: Bandit Tuning (Adaptive Optimization)

**What it does:** Uses multi-armed bandit to learn Q-values for each c incrementally.

```bash
python3 tune_c_bandit.py --episodes 50
```

**Command-line options:**
```bash
--episodes 50          # Default: 50 episodes (50 matches total)
--epsilon 0.3          # Initial exploration rate (default 0.3)
--decay 0.995          # Epsilon decay per episode (default 0.995)
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
BANDIT-BASED PARAMETER TUNING
═══════════════════════════════════════════════════════════════════════════════

Configuration:
  c values: [0.0, 0.1, ..., 1.0]
  opponents: [starter_baseline, defensive_opponent, aggressive_opponent]
  episodes: 50
  epsilon (initial): 0.300
  epsilon decay: 0.995

Running 50 episodes...

[Episode   1] c=0.50, opp=defensive_opponent, epsilon=0.300... reward=6.1, Q[c]=6.100
[Episode   2] c=0.85, opp=starter_baseline, epsilon=0.298... reward=2.3, Q[c]=2.300
[Episode   3] c=0.50, opp=aggressive_opponent, epsilon=0.296... reward=8.5, Q[c]=7.300
...
[Episode  50] c=0.65, opp=starter_baseline, epsilon=0.103... reward=9.2, Q[c]=7.850

✓ Per-episode results: results/tuning/bandit/bandit_results.csv
✓ Summary by c: results/tuning/bandit/bandit_summary.csv
✓ Best c (bandit): results/tuning/bandit/best_c_bandit.json

c        Pulls  Win Rate  Avg Diff  Final Q
──────────────────────────────────────────────
0.0      2      0.0%      -2.1     -2.100
...
0.65     6      83.3%     8.2      7.850  ★
0.7      5      80.0%     7.8      7.620
...

★ BEST: c = 0.65  (Q = 7.850)

Next step: python3 test_selected_c.py
```

**Time estimate:** ~30 minutes (50 episodes × 30-40s per match)

**Output files:**
- `results/tuning/bandit/bandit_results.csv` — Per-episode record
- `results/tuning/bandit/bandit_summary.csv` — Aggregated by c
- `results/tuning/bandit/best_c_bandit.json` — Selected c value
- `results/tuning/bandit/replays/` — All match recordings

**Compare with Grid Search:**
- Did bandit converge to similar c as grid search?
- How many total episodes did bandit run vs grid (50 vs 99)?
- Which method found higher-performing c?

---

### Phase 3: Testing on Held-Out Opponents

**What it does:** Validates that tuned c values generalize to test opponents.

```bash
python3 test_selected_c.py --matches 10
```

**Command-line options:**
```bash
--matches 10   # Default: 10 matches per c per test opponent
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
TESTING TUNED PARAMETERS ON HELD-OUT OPPONENTS
═══════════════════════════════════════════════════════════════════════════════

Test opponents: [balanced_opponent]
Matches per c: 10

✓ Loaded grid search best_c: 0.70
✓ Loaded bandit best_c: 0.65

Testing 6 c values (1 test opponents):

Testing c=0.10 (defensive)...
  vs balanced_opponent  match  1/10... ✓ (+3.2)
  vs balanced_opponent  match  2/10... ✓ (+2.1)
  ...

Testing c=0.50 (balanced)...
  ...

Testing c=0.65 (bandit)...
  ...

Testing c=0.70 (grid)...
  ...

✓ Per-match results: results/testing/test_results.csv
✓ Summary by c: results/testing/test_summary.csv
✓ Comparison: results/testing/test_comparison.json

c      Label        Win Rate  Avg Diff
─────────────────────────────────────────
0.10   defensive    30.0%     1.5
0.50   balanced     50.0%     3.2
0.65   bandit       80.0%     7.8  ★
0.70   grid         75.0%     7.2
0.90   aggressive   40.0%     2.1

★ BEST ON TEST SET: c = 0.65 (bandit)
   Win rate: 80.0%
   Avg score diff: 7.8

Next step: python3 plot_tuning_results.py
```

**Time estimate:** ~20 minutes (60 matches × 30-40s per match)

**Output files:**
- `results/testing/test_results.csv` — Per-match on test opponents
- `results/testing/test_summary.csv` — Aggregated by c
- `results/testing/test_comparison.json` — Best c + baselines
- `results/testing/replays/` — All test match recordings

**Key insights:**
- Does tuned c (grid/bandit) beat fixed baselines?
- Does bandit or grid perform better on test set?
- How much generalization gap exists?

---

### Phase 4: Generate Visualizations

**What it does:** Creates 7 presentation-ready PNG charts.

```bash
python3 plot_tuning_results.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
GENERATING PRESENTATION PLOTS
═══════════════════════════════════════════════════════════════════════════════

Generating plots...

✓ results/figures/training_heatmap_score_diff.png
✓ results/figures/training_winrate_by_c.png
✓ results/figures/training_score_diff_by_c.png
✓ results/figures/bandit_learning_curve.png
✓ results/figures/bandit_q_values_by_c.png
✓ results/figures/test_comparison.png
✓ results/figures/generalization_heatmap.png

✓ All plots saved to: results/figures/

Next step: python3 experiment_summary.py
```

**Time estimate:** <5 minutes

**Output files:**
- `results/figures/training_heatmap_score_diff.png` — Heatmap of c × opponent
- `results/figures/training_winrate_by_c.png` — Bar chart of win rates
- `results/figures/training_score_diff_by_c.png` — Bar chart of score diffs
- `results/figures/bandit_learning_curve.png` — Bandit convergence over episodes
- `results/figures/bandit_q_values_by_c.png` — Final learned values
- `results/figures/test_comparison.png` — Test set performance comparison
- `results/figures/generalization_heatmap.png` — Win rate on test opponents

**For presentation:**
- Use `training_heatmap_score_diff.png` to show parameter landscape
- Use `test_comparison.png` to show tuned c beats baselines
- Use `bandit_learning_curve.png` to explain adaptive optimization

---

### Phase 5: Generate Comprehensive Summary

**What it does:** Writes a markdown report synthesizing all results.

```bash
python3 experiment_summary.py
```

**Expected output:**
```
═══════════════════════════════════════════════════════════════════════════════
GENERATING EXPERIMENT SUMMARY
═══════════════════════════════════════════════════════════════════════════════

✓ Summary written to: experiment_summary.md

To view: open experiment_summary.md
```

**Time estimate:** <1 minute

**Output files:**
- `experiment_summary.md` — Full experiment report with:
  - Overview and bot design
  - Methodology (grid search + bandit)
  - Training results with tables
  - Testing results with generalization analysis
  - Key findings and conclusions
  - Limitations and future directions
  - Reproducibility instructions
  - Terminology clarification

---

## Complete Execution (All Phases)

**Run all steps sequentially:**

```bash
echo "Starting full tuning pipeline..."

echo "[1/5] Grid search..."
python3 tune_c_grid.py
if [ $? -ne 0 ]; then echo "Grid search failed"; exit 1; fi

echo -e "\n[2/5] Bandit tuning..."
python3 tune_c_bandit.py --episodes 50
if [ $? -ne 0 ]; then echo "Bandit failed"; exit 1; fi

echo -e "\n[3/5] Testing..."
python3 test_selected_c.py --matches 10
if [ $? -ne 0 ]; then echo "Testing failed"; exit 1; fi

echo -e "\n[4/5] Plotting..."
python3 plot_tuning_results.py
if [ $? -ne 0 ]; then echo "Plotting failed"; exit 1; fi

echo -e "\n[5/5] Summary..."
python3 experiment_summary.py
if [ $? -ne 0 ]; then echo "Summary failed"; exit 1; fi

echo -e "\n✓ Pipeline complete!"
echo "View results: open experiment_summary.md"
echo "View plots: open -a Preview results/figures/"
```

**Total time:** ~2-3 hours (includes 99 grid + 50 bandit + 60 test matches)

---

## Interpreting Results

### Success Criteria

✅ **Parameter tuning is working if:**
1. Best c is NOT an extreme value (0.0 or 1.0)
2. Best c win rate > baseline win rates (e.g., >50%)
3. Test set performance is similar to training (no overfitting)
4. Grid and bandit methods converge to similar c values

### Understanding the Outputs

**tuning_results.csv / bandit_results.csv:**
```
c: aggression parameter value
opponent: which opponent this match was against
score_diff: agent_score - opponent_score (positive = agent won by margin)
win: 1 if agent won, 0 if lost
turns: how long the game lasted
```

**tuning_summary.csv / bandit_summary.csv:**
```
c: aggression value
num_games / pulls: how many times this c was evaluated
win_rate: fraction of matches won with this c
avg_score_diff: average score advantage
```

**test_comparison.json:**
```json
{
  "best_c_on_test": {
    "c": 0.65,              // Best c value on test set
    "c_label": "bandit",    // Which method found it
    "win_rate": 0.8,        // Performance on test opponents
    "avg_score_diff": 7.8   // Average advantage
  }
}
```

### Key Questions to Answer

1. **Does tuning help?** Compare tuned c's test performance vs baselines (c=0.1, 0.5, 0.9)
2. **Which method works better?** Compare grid vs bandit on test set
3. **Does it generalize?** Is test performance similar to training?
4. **What's the improvement?** How much better is best c vs worst c?
5. **Is it robust?** Do multiple runs produce similar results?

---

## Customization

### To test different c ranges:

Edit `experiment_config.json`:
```json
"c_values": [0.0, 0.05, 0.1, ..., 1.0]  // Finer granularity
```

### To add more training opponents:

1. Create opponent bot: `mkdir opponents/my_opponent`
2. Copy bot code and create `run.sh` with `export AGGRESSION=X.XX`
3. Add to `experiment_config.json`:
   ```json
   "train_opponents": [..., "my_opponent"]
   ```

### To run longer/shorter:

```bash
# Fewer matches (quick test)
python3 tune_c_grid.py        # Uses config default (3 games/combo)

# Longer grid search (more robust)
# Edit experiment_config.json: "games_per_c_per_opponent": 10

# Longer bandit
python3 tune_c_bandit.py --episodes 200

# More test matches
python3 test_selected_c.py --matches 20
```

---

## Troubleshooting

### Issue: Matches hang or never finish
**Solution:** 
- Check engine.jar is executable: `java -jar engine.jar --version`
- Increase timeout in scripts (line: `timeout=300`)
- Run one match manually: `java -jar engine.jar work opponents/starter_baseline/run.sh python-algo/run.sh`

### Issue: "endStats not found" in replay parsing
**Solution:**
- Check replay file exists in `replays/`
- Verify replay has valid JSON lines
- Check that game actually completed (not timeout)

### Issue: Matplotlib/pandas import error
**Solution:**
```bash
pip install matplotlib pandas numpy
```

### Issue: Tests all lose (win_rate = 0%)
**Solution:**
- Check opponent bots are actually running
- Verify bot logic (check `algo_strategy.py` in opponent folders)
- Increase c value (try c=0.9 for more aggressive play)

---

## File Reference

### Main Scripts
- `tune_c_grid.py` — Grid search over parameter space (~350 lines)
- `tune_c_bandit.py` — Epsilon-greedy bandit optimization (~280 lines)
- `test_selected_c.py` — Evaluation on held-out opponents (~280 lines)
- `plot_tuning_results.py` — Visualization generation (~350 lines)
- `experiment_summary.py` — Documentation generation (~300 lines)

### Configuration
- `experiment_config.json` — Define tuning parameters and opponents

### Documentation
- `TUNING_README.md` — Comprehensive reference guide
- `experiment_summary.md` — Generated after running pipeline

### Opponent Bots
- `opponents/{starter_baseline, defensive_opponent, balanced_opponent, aggressive_opponent}/`

### Results (Auto-Generated)
- `results/tuning/grid/` — Grid search outputs
- `results/tuning/bandit/` — Bandit outputs
- `results/testing/` — Testing outputs
- `results/figures/` — Visualization PNGs

---

## Next Steps After Running

1. **Review experiment_summary.md** — Comprehensive report of all results
2. **Check results/figures/** — View charts for presentation
3. **Analyze test_summary.csv** — See if tuned c beats baselines
4. **Consider questions:**
   - How much improvement does tuning provide?
   - Does grid or bandit work better?
   - Should we test more opponents?
   - Should we try different parameter ranges?

---

**Ready to run? Start with:**

```bash
python3 tune_c_grid.py
```
