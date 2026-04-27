# Opponent Bot Set

This folder contains different opponent variants used for parameter tuning.

Each opponent is a self-contained bot that can be launched by the C1 Terminal engine.

## Opponents

### 1. starter_baseline
**Type:** Balanced baseline
**Description:** Unmodified C1 starter algorithm
**Launch:** `opponents/starter_baseline/run.sh`

### 2. defensive_opponent
**Type:** Heavily defensive
**Description:** Our bot with AGGRESSION=0.1 (turtles, builds lots of walls)
**Strategy:** Prioritizes defense, minimal early offense
**Use case:** Training agent to handle defensive opponents

### 3. balanced_opponent
**Type:** Balanced strategy
**Description:** Our bot with AGGRESSION=0.5 (baseline)
**Strategy:** Mix of offense and defense
**Use case:** Training/testing against a moderate opponent

### 4. aggressive_opponent
**Type:** Heavily offensive
**Description:** Our bot with AGGRESSION=0.85 (rushes early)
**Strategy:** Prioritizes offense, minimal defense
**Use case:** Training agent to handle aggressive threats

### 5. random_aggression_opponent
**Type:** Variable
**Description:** Our bot with randomized AGGRESSION sampled from [0.0, 1.0]
**Strategy:** Unpredictable behavior
**Use case:** Robustness testing

### 6. mixed_strategy_opponent
**Type:** Hybrid
**Description:** Our bot with AGGRESSION sampled per-match from fixed set {0.2, 0.5, 0.8}
**Strategy:** Forces adaptation to varied playing styles
**Use case:** Generalization testing

## Usage

All opponents follow the standard C1 Terminal interface:
```bash
java -jar engine.jar work <our_agent>/run.sh opponents/<opponent_name>/run.sh
```

The engine will:
1. Start our agent as the first player (P1)
2. Start the opponent as the second player (P2)
3. Write replay to `replays/<timestamp>.replay`

## Adding New Opponents

To add a new opponent:
1. Create a folder: `opponents/new_opponent/`
2. Copy `algo.json`, `algo_strategy.py`, and `run.sh` from python-algo/
3. Modify `run.sh` to set the desired behavior (either via AGGRESSION or STRATEGY env var, or by editing algo_strategy.py directly)
4. Document it in this README
