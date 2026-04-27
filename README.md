# Terminal Algo Strategy — project overview

CS 3501: AI & Humanity (Spring 2026) — Professor David Evans

This repository contains the code, experiments, and documentation for our group's project investigating how a single tunable objective parameter changes an agent's behavior in the C1 Terminal environment. Rather than changing the agent's implementation, we vary one scalar (called `aggression` or `c`) and run many head-to-head matches to measure the behavioural and performance effects.

High-level goals
- Show how small changes to an objective (single parameter) produce large, non-linear behavioral differences.
- Produce reproducible experiments (grid search, bandit tuning, held-out testing).
- Produce presentation-ready artifacts (figures + slide-plan) and speaker notes for a class presentation.

Contents at-a-glance
- `python-algo/` — the rule-based agent code. The agent reads `AGGRESSION` from the environment and uses it to interpolate strategy weights.
- `opponents/` — small set of opponent configurations (run.sh files that set different `AGGRESSION` presets).
- `scripts/` — helper scripts for engine integration and quick tests.
- `tune_c_grid.py` — grid search orchestration (runs many matches, aggregates per-c metrics).
- `tune_c_bandit.py` — epsilon-greedy bandit tuner (learns good c values online).
- `test_selected_c.py` — held-out evaluation harness for best c candidates.
- `plot_tuning_results.py` — generates presentation-ready PNG charts under `results/figures/`.
- `experiment_config.json` — single source of truth for experiment parameters (c grid, opponents, games per combo).
- `run_tuning_pipeline.sh` — orchestration script that runs the full pipeline (grid → bandit → test → plot → report).
- `results/` — output folder (CSV, JSON, PNG) produced by the pipeline.
- `README.md` — this file (how to run, expectations, file index, next steps).

Why this is interesting
- We're not training a neural network; we're systematically changing one objective scalar and showing that behavior and outcomes can change radically despite identical code paths. This produces a clean demonstration for discussions about reward design and robustness.

Quick start — prerequisites
- macOS or Linux, Python 3.8+, and Java (jdk 17/21+). The engine is invoked via `java -jar engine.jar`.
- Confirm these are available before running the pipeline.

Sanity checks (example)
```bash
# confirm Python and Java
python3 --version
java -version

# quick algorithm test script provided for mac/linux
./scripts/test_algo_mac python-algo/   # or use test_algo_linux on Linux
```

Run the full automated tuning pipeline
- This repository contains an end-to-end orchestration that executes:
  1. Grid search over c values (writes `results/tuning/grid/`)
 2. Epsilon-greedy bandit tuning (writes `results/tuning/bandit/`)
 3. Held-out testing on specified test opponents (writes `results/testing/`)
 4. Plotting and figure generation (writes `results/figures/`)
 5. A short `experiment_summary.md` with key results and recommended slides

Run it from the repository root:
```bash
bash run_tuning_pipeline.sh
```

Expected runtimes (rough)
- Phase 1 — Grid search: ~60 minutes (config: 11 c values × 3 training opponents × 3 runs each in the default config). This varies with machine and engine speed.
- Phase 2 — Bandit tuning: ~30 minutes (default: 50 episodes in epsilon-greedy).
- Phase 3 — Testing: ~20 minutes (held-out opponents, configurable).
- Phase 4 — Visualization: < 5 minutes.
- Phase 5 — Summary generation: < 1 minute.

If you prefer to run a single stage (fast):
```bash
# Only run grid search (example)
python3 tune_c_grid.py --config experiment_config.json

# Only run plotting (after results exist)
python3 plot_tuning_results.py --results results/tuning/grid/
```

Important output artifacts
- `results/tuning/grid/tuning_results.csv` — per-match records produced by the grid search.
- `results/tuning/grid/tuning_summary.csv` — aggregated metrics per `c`.
- `results/tuning/grid/best_c.json` — best candidate(s) chosen from the grid stage.
- `results/tuning/bandit/` — bandit logs, Q-values, and summaries.
- `results/testing/test_results.csv` & `results/testing/test_summary.csv` — held-out evaluation outputs.
- `results/figures/` — PNG charts ready to drop into slides.
- `experiment_summary.md` — short report that the pipeline also writes for presentation use.

How matches are run (implementation notes)
- Each agent/opponent is invoked via a small `run.sh` wrapper which sets `AGGRESSION` and then executes the Python agent: `python3 python-algo/algo_strategy.py`.
- Matches are launched by calling the Java engine: `java -jar engine.jar work <agent1_run_sh> <agent2_run_sh>` which produces a `.replay` JSON file. The analyzer reads the last replay to extract `endStats` and aggregates metrics.

Metrics we track
- Primary: average score difference (agent_score - opponent_score) — useful when games end at fixed max turns.
- Secondary: win rate, average game length (turns), finer resource breakdowns (in per-match CSVs).

File index (important files)
- `python-algo/algo_strategy.py` — agent entry point; reads `AGGRESSION` env var and computes decisions.
- `opponents/*/run.sh` — opponent presets (each exports `AGGRESSION` for that opponent config).
- `experiment_config.json` — controls grid values, opponent lists, repeats, and other tuning parameters.
- `run_tuning_pipeline.sh` — run everything (pre-flight checks + sequential phases).
- `tune_c_grid.py`, `tune_c_bandit.py`, `test_selected_c.py`, `plot_tuning_results.py` — core pipeline scripts.
- `results/` — where all outputs will appear.
- `TUNING_README.md` — more detailed developer notes on tuning scripts.

What to look at when the pipeline finishes
- The single-file summaries: `results/tuning/grid/tuning_summary.csv` and `results/testing/test_summary.csv`.
- `results/figures/` — copy the PNGs directly into slides. Typical figure names include: `winrate_by_c.png`, `score_diff_by_c.png`, `bandit_q_values.png`, `test_comparison.png`, etc.
- `experiment_summary.md` — short summary + suggested slide order and talking points (auto-generated by the pipeline).

Notes for collaborators / slide production
- The pipeline creates a `experiment_summary.md` that contains a suggested slide plan and a brief script for each slide. I recommend copying that into the slide-plan document and placing the corresponding PNGs from `results/figures/` into each slide.
- If you want me to also draft the actual slides, say so in the channel — I can create a first-pass deck with placeholders and then add speaker notes.

Troubleshooting
- If the engine can't be found, make sure `engine.jar` is in the repo root or adjust the path used by `run_tuning_pipeline.sh`.
- If replays are not being written, check the Java process output in the terminal where you ran the pipeline; the analyzer expects `endStats` in the replay JSON.

Next steps / roadmap
- Run the full pipeline and inspect outputs (figures + `experiment_summary.md`).
- If needed: run a fine-grained sweep around the discovered sweet spot (e.g., 0.35–0.65) to find transition points.
- Prepare slides from the slide-plan doc and ask me to add comprehensive speaker notes.

License / origin
- Forked from the [C1GamesStarterKit](https://github.com/correlation-one/C1GamesStarterKit). The `gamelib/` folder and helper scripts are adapted from their starter kit.
