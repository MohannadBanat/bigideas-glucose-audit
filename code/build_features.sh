#!/usr/bin/env bash
# Stream the E4 files participant by participant from the AWS mirror (v1.1.2;
# E4 files are byte-identical in v1.1.3), verify them against the v1.1.3
# SHA256SUMS, build that participant's feature table, then delete the raw
# files. Peak disk use is one participant (~2.6 GB).
#
#   ./code/build_features.sh SMALL_ROOT OUT_DIR [TMP_DIR] [PID ...]
set -euo pipefail
SMALL="$1"; OUT="$2"; TMP="${3:-./data/e4_tmp}"; shift $(( $# < 3 ? $# : 3 ))
PIDS=("$@"); [[ ${#PIDS[@]} -eq 0 ]] && PIDS=($(seq -f "%03g" 1 16))
S3="https://physionet-open.s3.amazonaws.com/big-ideas-glycemic-wearable/1.1.2"
HERE="$(cd "$(dirname "$0")" && pwd)"
for p in "${PIDS[@]}"; do
  mkdir -p "$TMP/$p"
  for s in ACC BVP EDA HR IBI TEMP; do
    [[ -s "$TMP/$p/${s}_$p.csv" ]] || curl -sSf --retry 4 -o "$TMP/$p/${s}_$p.csv" "$S3/$p/${s}_$p.csv"
  done
  (cd "$TMP" && grep -E " $p/(ACC|BVP|EDA|HR|IBI|TEMP)_" "$SMALL/SHA256SUMS.txt" | sha256sum -c --quiet -)
  python3 "$HERE/features.py" "$TMP" "$SMALL" "$OUT" "$p"
  rm -rf "${TMP:?}/$p"
done
echo "all done"
