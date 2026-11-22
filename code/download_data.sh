#!/usr/bin/env bash
# Download BIG IDEAs Lab Glycemic Variability and Wearable Device Data v1.1.3
# from physionet.org (open access, ODC-By 1.0; no account needed).
#
# NOTE: the AWS mirror s3://physionet-open/big-ideas-glycemic-wearable/ stops at
# v1.1.2 (checked 22 Nov 2026). v1.1.3 fixes misaligned food-log dates, so use
# physionet.org, not the mirror.
#
#   ./code/download_data.sh [DEST]          small files only (food logs, Dexcom,
#                                           demographics; ~2.5 MB) - enough for
#                                           check_time_of_day.py
#   ./code/download_data.sh [DEST] --full   everything (~34 GB uncompressed)
set -euo pipefail

DEST="${1:-./data/big-ideas-1.1.3}"
MODE="${2:-}"
BASE="https://physionet.org/files/big-ideas-glycemic-wearable/1.1.3"
mkdir -p "$DEST"
cd "$DEST"

if [[ "$MODE" == "--full" ]]; then
  wget -r -N -c -np -nH --cut-dirs=3 "$BASE/"
else
  curl -sSf -O "$BASE/Demographics.csv" -O "$BASE/SHA256SUMS.txt"
  for i in $(seq -w 1 16); do
    p="0$i"
    mkdir -p "$p"
    (cd "$p" && curl -sSf -O "$BASE/$p/Food_Log_$p.csv" && curl -sSf -O "$BASE/$p/Dexcom_$p.csv")
  done
fi

# Verify whatever was downloaded against the published checksums.
grep -E "$( [[ "$MODE" == "--full" ]] && echo '.' || echo 'Food_Log|Dexcom|Demographics' )" SHA256SUMS.txt \
  | (command -v sha256sum >/dev/null && sha256sum -c --quiet - || shasum -a 256 -c --quiet -)
echo "Done and checksums OK: $DEST"
