#!/usr/bin/env bash
# Dev helper: fresh sim + controller + grade for one scenario.  usage: ./rerun.sh public_01_dev
set -e
S=${1:-public_01_dev}; N=${S%%_*}_${S#*_}; N=$(echo "$S" | cut -d_ -f1-2)
cd "$(dirname "$0")"
export PYTHONUTF8=1
rm -rf runs/mine_$N controller_$N.db*
python -m sim serve --scenario scenarios/$S.yaml --run-dir runs/mine_$N > sim_$N.log 2>&1 &
SP=$!; for i in $(seq 1 120); do curl -sf http://127.0.0.1:8700/health >/dev/null && break; sleep 1; done
S0=$(date +%s); CONTROLLER_DB=controller_$N.db bash run.sh http://127.0.0.1:8700 | tail -1; echo wall_seconds=$(( $(date +%s)-S0 ))
kill $SP 2>/dev/null || true
[ -d runs/base_$N ] || python -m sim baseline --scenario scenarios/$S.yaml --run-dir runs/base_$N | tail -1
python -m sim grade --run runs/mine_$N --baseline runs/base_$N --out reports/$N.md > /dev/null
sed -n '3,12p;/Changes applied/,/## Governance/p' reports/$N.md
