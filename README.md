# Terminal Algo Strategy

**CS 3501: AI & Humanity (Spring 2026) — Professor David Evans**

This is our group's project for the class. The basic idea is that we wanted to explore how changing an AI agent's objective function actually changes the way it behaves not just in theory, but in a real environment where you can watch it play and measure what happens.

We used [C1 Terminal](https://terminal.c1games.com/) as the testbed, which is a tower defense programming game where two bots compete. It turned out to be a pretty good sandbox for this kind of concept since the outcomes are concrete and measurable.

---

## What we're actually doing

The agent has one tunable parameter called `aggression` (a float from 0.0 to 1.0). It controls how the bot weighs offense vs. defense in every decision it makes. At 0.0 it basically just turtles and builds walls forever. At 1.0 it rushes as hard as it can and ignores defense almost entirely. Everything in between is a linear interpolation.

The code itself doesn't change between runs, it is the same decision pipeline every time:

1. Look at the board (health, resources, what the enemy is doing)
2. Build/upgrade defenses if needed
3. Decide whether to attack and how

The only thing that changes is that one number.

Here's a rough summary of what different aggression values look like in practice:

| aggression | Style | MP Threshold | Upgrades? | Supports? | Early Stall Turns | Scout Rush? |
|:----------:|:-----:|:-----------:|:---------:|:---------:|:-----------------:|:-----------:|
| 0.0 | Full Defense defense | 18 | ✅ | ❌ | 8 | ❌ |
| 0.5 | Balanced | 11.5 | ✅ | ✅ | 5 | ✅ |
| 1.0 | Full Offense offense | 5 | ❌ | ✅ | 2 | ✅ |

All weights are interpolated with `_lerp(defense_val, offense_val, aggression)`.

### Key files

```
python-algo/
  algo_strategy.py        # main entry point, reads AGGRESSION env var
  strategies/
    base_strategy.py      # all the actual logic + parameter weights
    baseline.py           # preset at aggression = 0.50
    offense.py            # preset at aggression = 0.85
    defense.py            # preset at aggression = 0.15
  gamelib/                # C1 SDK, didn't touch this

python-algo-starter/      # the fixed opponent we test against

run_sweep.py              # runs all the matches across aggression values
analyze_results.py        # parses replays into CSVs
plot_results.py           # generates graphs from the CSVs
sweep_results.csv         # raw per-match data
sweep_summary.csv         # averages by aggression level
graphs/                   # all the output charts
REWARD_FUNCTION.md        # more detailed writeup of the objective function
```

---

## How to Run

You need Python 3 and Java 21+ installed.

```bash
# quick sanity check (no Java needed)
./scripts/test_algo_mac python-algo/

# Run a single match
java -jar engine.jar work python-algo/run.sh python-algo-starter/run.sh

# Run the full sweep (this takes a while)
python3 run_sweep.py --repeats 10

# Analyze the replays
python3 analyze_results.py

# Generate graphs
python3 plot_results.py
```

You can also test specific aggression values:
```bash
AGGRESSION=0.4 ./scripts/test_algo_mac python-algo/
```

---

## Results

We ran 10 matches at each of 11 aggression levels (110 total). All against the same fixed starter opponent.

![heatmap](sweep_heatmap.png)

| Aggression | Win% | Avg Agent Pts | Avg Opp Pts | Avg Turns |
|:---:|:---:|:---:|:---:|:---:|
| 0.0 | 100% | 8.3 | 4.1 | 100 |
| 0.1 | 80% | 7.1 | 8.3 | 99.5 |
| 0.2 | 30% | 7.3 | 23.1 | 97.8 |
| 0.3 | 0% | 4.2 | 43.4 | 60.6 |
| 0.4 | 100% | 48.3 | 12.9 | 43.2 |
| 0.5 | 100% | 44.0 | 2.6 | 33.4 |
| 0.6 | 90% | 49.4 | 28.8 | 24.8 |
| 0.7 | 0% | 9.6 | 40.7 | 16.3 |
| 0.8 | 10% | 10.9 | 37.2 | 24.7 |
| 0.9 | 0% | 13.2 | 45.6 | 13.3 |
| 1.0 | 0% | 10.2 | 46.8 | 11.0 |

A few things stood out to us:

- **0.4–0.6 is clearly the sweet spot.** These agents win consistently, score the most, and end games fast. The fully defensive agents at 0.0–0.1 technically "win" a lot but only because the opponent is weak — they score almost nothing and games drag to turn 100.

- **There's a weird valley at 0.3** where performance drops to 0% even though 0.2 and 0.4 both do better. It's too aggressive to turtle properly but not aggressive enough to actually win fights. Worst of both worlds.

- **The drop from 0.6 to 0.7 is really sharp** — goes from 90% win rate to 0% with just a 0.1 shift in the parameter. Nothing in the code changes, just that one number.

- **Full offense (0.7–1.0) collapses fast.** Games end by turn 11–16 because the bot has no structure to survive counterattacks. It's spending resources on offense but can't even execute attacks before it loses.

More graphs are in the `graphs/` folder if you want to look at resource allocation, score breakdowns, etc.

---

## Next Steps

- Test against a stronger or different opponent to see if the sweet spot shifts
- Maybe do a finer sweep around 0.35–0.65 to find the exact transition points
- The alignment writeup is in `REWARD_FUNCTION.md` if you want the more formal framing

---

## Original Starter Kit

Forked from the [C1GamesStarterKit](https://github.com/correlation-one/C1GamesStarterKit). The `gamelib/` folder and most of `scripts/` are unchanged from the original. See their docs if you need help with the engine setup.
