#!/bin/bash
export AGGRESSION=0.5
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
${PYTHON_CMD:-python3} -u "$DIR/algo_strategy.py"
