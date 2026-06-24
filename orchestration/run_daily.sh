#!/usr/bin/env bash
# Daily entrypoint for the Cloud Run Job.
#
# Derives the month to load from the run date, ingests it idempotently, then
# runs dbt build which rebuilds only the new partitions and refreshes the marts.
# Any failure stops the run with a non-zero exit so the scheduler can alert.

set -euo pipefail

: "${GCP_PROJECT:=massive-network-500412-u2}"
: "${GCS_BUCKET:=nyc-taxi-landing-massive-network-500412-u2}"
: "${BQ_DATASET:=nyc_taxi}"

# TLC data lags real time, so load the month two months back by default.
# Override with TARGET_MONTH for backfills.
TARGET_MONTH="${TARGET_MONTH:-$(date -u -d '2 months ago' +%Y-%m)}"

echo "Run date: $(date -u +%Y-%m-%d). Target month: ${TARGET_MONTH}"

python ingestion/ingest.py --month "${TARGET_MONTH}"

cd dbt
dbt build --target prod

echo "Daily run complete for ${TARGET_MONTH}"
