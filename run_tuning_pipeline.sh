#!/bin/bash
# Quick-start execution script for the tuning pipeline
# Usage: bash run_tuning_pipeline.sh

set -e  # Exit on error

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  C1 Terminal - Aggression Parameter Tuning Pipeline           ║"
echo "║  ============================================================ ║"
echo "║  This script runs all tuning phases in sequence               ║"
echo "║  Total time: ~2-3 hours (99 grid + 50 bandit + 60 test)      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
echo "[PRE-FLIGHT CHECK]"
echo ""

if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found"
    exit 1
fi
echo "✓ python3 installed"

if ! command -v java &> /dev/null; then
    echo "ERROR: java not found"
    exit 1
fi
echo "✓ java installed"

if [ ! -f engine.jar ]; then
    echo "ERROR: engine.jar not found in $ROOT"
    exit 1
fi
echo "✓ engine.jar found"

if [ ! -f experiment_config.json ]; then
    echo "ERROR: experiment_config.json not found"
    exit 1
fi
echo "✓ experiment_config.json found"

echo ""
echo "[PHASE 1: GRID SEARCH]"
echo "Evaluating 11 c values × 3 opponents × 3 runs = 99 matches"
echo "Time: ~60 minutes"
echo ""

if python3 tune_c_grid.py; then
    echo "✓ Grid search complete"
else
    echo "✗ Grid search failed"
    exit 1
fi

echo ""
echo "[PHASE 2: BANDIT TUNING]"
echo "Running 50 episodes with epsilon-greedy bandit"
echo "Time: ~30 minutes"
echo ""

if python3 tune_c_bandit.py --episodes 50; then
    echo "✓ Bandit tuning complete"
else
    echo "✗ Bandit tuning failed"
    exit 1
fi

echo ""
echo "[PHASE 3: TESTING]"
echo "Evaluating best c values on held-out test opponents"
echo "Time: ~20 minutes"
echo ""

if python3 test_selected_c.py --matches 10; then
    echo "✓ Testing complete"
else
    echo "✗ Testing failed"
    exit 1
fi

echo ""
echo "[PHASE 4: VISUALIZATION]"
echo "Generating 7 presentation-ready plots"
echo "Time: <5 minutes"
echo ""

if python3 plot_tuning_results.py; then
    echo "✓ Visualization complete"
else
    echo "✗ Visualization failed"
    exit 1
fi

echo ""
echo "[PHASE 5: DOCUMENTATION]"
echo "Generating comprehensive experiment summary"
echo "Time: <1 minute"
echo ""

if python3 experiment_summary.py; then
    echo "✓ Documentation complete"
else
    echo "✗ Documentation failed"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  ✓ PIPELINE COMPLETE                                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "Results are organized in:"
echo ""
echo "├── results/tuning/grid/          Grid search results"
echo "├── results/tuning/bandit/        Bandit learning results"
echo "├── results/testing/              Test set evaluation"
echo "└── results/figures/              7 presentation plots"
echo ""
echo "Summary report:"
echo "  open experiment_summary.md"
echo ""
echo "View plots:"
echo "  open results/figures/"
echo ""
echo "Next steps:"
echo "  1. Review experiment_summary.md"
echo "  2. Check if tuned c beats baselines in results/testing/test_summary.csv"
echo "  3. Use charts from results/figures/ for presentation"
echo ""
