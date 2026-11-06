#!/usr/bin/env bash
# Contract: ./run.sh <SIM_URL> runs until the scenario finishes. No Docker needed; plain Python 3.10+.
set -euo pipefail
SIM_URL="${1:?usage: ./run.sh <SIM_URL>}"
cd "$(dirname "$0")"
exec python -m controller.main --url "$SIM_URL" --db "${CONTROLLER_DB:-controller.db}"
