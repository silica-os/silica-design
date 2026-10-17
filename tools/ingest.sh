#!/bin/sh
# usage: ingest.sh <scratch-dir> <batch-name>   (takes the newest saved run_code result)
set -e
T=$(ls -t "$HOME"/.claude/projects/*/*/tool-results/mcp-sketch-run_code-*.txt | head -1)
D=$(dirname "$0")
python3 "$D/grab.py" "$T" "$1/$2.json"
python3 "$D/build_kit.py" master "$1/$2.json" "$1/stage"
