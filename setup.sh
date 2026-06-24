#!/usr/bin/env bash
# Local end-to-end setup and run.
#
# Provisions the GCS bucket and BigQuery dataset, prepares a Python virtual
# environment, loads the zone dimension, ingests one month, and runs dbt.
# Safe to re-run: every step is idempotent.
#
# Usage:
#   source .env        # or: export GCP_PROJECT=... GCS_BUCKET=... BQ_DATASET=...
#   ./setup.sh 2023-01

set -euo pipefail

MONTH="${1:-2023-01}"

: "${GCP_PROJECT:?Set GCP_PROJECT (run: source .env)}"
: "${GCS_BUCKET:?Set GCS_BUCKET (run: source .env)}"
: "${BQ_DATASET:=nyc_taxi}"
: "${BQ_LOCATION:=US}"

echo "Project:  ${GCP_PROJECT}"
echo "Bucket:   ${GCS_BUCKET}"
echo "Dataset:  ${BQ_DATASET} (${BQ_LOCATION})"
echo "Month:    ${MONTH}"
echo

echo "Step 1: confirm gcloud auth and project"
gcloud config set project "${GCP_PROJECT}" >/dev/null
gcloud auth application-default print-access-token >/dev/null 2>&1 || {
    echo "No application-default credentials found. Running login..."
    gcloud auth application-default login
}

echo "Step 2: enable required APIs (idempotent)"
gcloud services enable bigquery.googleapis.com storage.googleapis.com >/dev/null

echo "Step 3: create the GCS landing bucket if missing"
if ! gcloud storage buckets describe "gs://${GCS_BUCKET}" >/dev/null 2>&1; then
    gcloud storage buckets create "gs://${GCS_BUCKET}" \
        --location="${BQ_LOCATION}" --uniform-bucket-level-access
else
    echo "  bucket already exists"
fi

echo "Step 4: create the BigQuery dataset if missing"
if ! bq --location="${BQ_LOCATION}" show "${GCP_PROJECT}:${BQ_DATASET}" >/dev/null 2>&1; then
    bq --location="${BQ_LOCATION}" mk --dataset "${GCP_PROJECT}:${BQ_DATASET}"
else
    echo "  dataset already exists"
fi

echo "Step 5: set up the Python environment"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r ingestion/requirements.txt
pip install --quiet "dbt-bigquery>=1.8.0"

echo "Step 6: load the zone dimension (once)"
python ingestion/load_zones.py

echo "Step 7: ingest the month (idempotent)"
python ingestion/ingest.py --month "${MONTH}"

echo "Step 8: build dbt models"
cd dbt
if [ ! -f profiles.yml ]; then
    cp profiles.example.yml profiles.yml
    echo "  copied dbt/profiles.yml from the example"
fi
DBT_PROFILES_DIR="$(pwd)" dbt build
cd ..

echo
echo "Done. The marts are in ${GCP_PROJECT}.${BQ_DATASET}."
echo "Run the queries in analysis/queries.sql in the BigQuery console."
