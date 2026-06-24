# Local end-to-end setup and run for Windows PowerShell.
#
# Provisions the GCS bucket and BigQuery dataset, prepares a Python virtual
# environment, loads the zone dimension, ingests one month, and runs dbt.
# Safe to re-run: every step is idempotent.
#
# Usage (from the repo root, in PowerShell):
#   .\setup.ps1 -Month 2023-01
#
# Values default to the project below; override with parameters if needed.

param(
    [string]$Month       = "2023-01",
    [string]$GcpProject  = "massive-network-500412-u2",
    [string]$GcsBucket   = "nyc-taxi-landing-massive-network-500412-u2",
    [string]$BqDataset   = "nyc_taxi",
    [string]$BqLocation  = "US"
)

$ErrorActionPreference = "Stop"

Write-Host "Project:  $GcpProject"
Write-Host "Bucket:   $GcsBucket"
Write-Host "Dataset:  $BqDataset ($BqLocation)"
Write-Host "Month:    $Month"
Write-Host ""

Write-Host "Step 1: confirm gcloud auth and project"
gcloud config set project $GcpProject | Out-Null

# Probe ADC without aborting: under $ErrorActionPreference=Stop the gcloud PS
# wrapper turns a non-zero exit into a terminating error, which would skip the
# login fallback. Relax the preference for the probe, then branch on the exit.
$ErrorActionPreference = "Continue"
gcloud auth application-default print-access-token 2>$null | Out-Null
$noAdc = $LASTEXITCODE -ne 0
$ErrorActionPreference = "Stop"
if ($noAdc) {
    Write-Host "No application-default credentials found. Running login..."
    gcloud auth application-default login
}

Write-Host "Step 2: enable required APIs (idempotent)"
gcloud services enable bigquery.googleapis.com storage.googleapis.com | Out-Null

Write-Host "Step 3: create the GCS landing bucket if missing"
# Same Stop-mode caveat as Step 1: the "not found" from the existence probe is
# raised as a terminating error, which would abort before the create branch.
$ErrorActionPreference = "Continue"
gcloud storage buckets describe "gs://$GcsBucket" 2>$null | Out-Null
$bucketMissing = $LASTEXITCODE -ne 0
$ErrorActionPreference = "Stop"
if ($bucketMissing) {
    gcloud storage buckets create "gs://$GcsBucket" --location=$BqLocation --uniform-bucket-level-access
} else {
    Write-Host "  bucket already exists"
}

Write-Host "Step 4: create the BigQuery dataset if missing"
$ErrorActionPreference = "Continue"
bq --location=$BqLocation show "${GcpProject}:${BqDataset}" 2>$null | Out-Null
$datasetMissing = $LASTEXITCODE -ne 0
$ErrorActionPreference = "Stop"
if ($datasetMissing) {
    bq --location=$BqLocation mk --dataset "${GcpProject}:${BqDataset}"
} else {
    Write-Host "  dataset already exists"
}

Write-Host "Step 5: set up the Python environment"
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r ingestion\requirements.txt
python -m pip install --quiet "dbt-bigquery>=1.8.0"

# Make the env vars available to the Python scripts in this session
$env:GCP_PROJECT = $GcpProject
$env:GCS_BUCKET  = $GcsBucket
$env:BQ_DATASET  = $BqDataset
$env:BQ_LOCATION = $BqLocation

Write-Host "Step 6: load the zone dimension (once)"
python ingestion\load_zones.py

Write-Host "Step 7: ingest the month (idempotent)"
python ingestion\ingest.py --month $Month

Write-Host "Step 8: build dbt models"
Push-Location dbt
if (-not (Test-Path "profiles.yml")) {
    (Get-Content profiles.example.yml) -replace "your-project-id", $GcpProject | Set-Content profiles.yml
    Write-Host "  generated dbt\profiles.yml from the example"
}
$env:DBT_PROFILES_DIR = (Get-Location).Path
dbt build
Pop-Location

Write-Host ""
Write-Host "Done. The marts are in ${GcpProject}.${BqDataset}."
Write-Host "Run the queries in analysis\queries.sql in the BigQuery console."
