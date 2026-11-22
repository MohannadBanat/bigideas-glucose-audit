#!/usr/bin/env bash
# Download BIG IDEAs Lab Glycemic Variability and Wearable Device Data v1.1.3
# ~34 GB uncompressed. Requires the AWS CLI (no AWS account needed).
# Alternative: wget -r -N -c -np https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3/
set -euo pipefail

DEST="${1:-./data/big-ideas-1.1.3}"
mkdir -p "$DEST"

aws s3 sync --no-sign-request \
  s3://physionet-open/big-ideas-glycemic-wearable/1.1.3/ "$DEST"

# Small files only (food logs, Dexcom, demographics) — enough for check_time_of_day.py:
# aws s3 sync --no-sign-request s3://physionet-open/big-ideas-glycemic-wearable/1.1.3/ "$DEST" \
#   --exclude "*" --include "*Food_Log*" --include "*Dexcom*" --include "Demographics.csv"

echo "Done: $DEST"
