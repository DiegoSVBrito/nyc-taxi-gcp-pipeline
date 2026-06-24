# Orchestration

The daily pipeline runs as a Cloud Run Job triggered by Cloud Scheduler. This
pairing was chosen over Cloud Composer because the workload is a single short
daily task. Composer keeps an environment running continuously at roughly 300
USD per month, which is not justified here. Scheduler plus a Cloud Run Job costs
close to nothing because it bills only for the seconds the job runs.

## Files

- `run_daily.sh` derives the target month from the run date and runs ingestion
  then `dbt build`.
- `Dockerfile` packages the ingestion code and dbt project into one small image.

## Deploy outline

```bash
# Build and push the image
gcloud builds submit --tag gcr.io/${GCP_PROJECT}/nyc-taxi-daily orchestration/

# Create the Cloud Run Job
gcloud run jobs create nyc-taxi-daily \
  --image gcr.io/${GCP_PROJECT}/nyc-taxi-daily \
  --region us-central1 \
  --set-env-vars GCP_PROJECT=${GCP_PROJECT},GCS_BUCKET=${GCS_BUCKET},BQ_DATASET=nyc_taxi

# Schedule it daily
gcloud scheduler jobs create http nyc-taxi-daily-trigger \
  --schedule "0 6 * * *" \
  --uri "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${GCP_PROJECT}/jobs/nyc-taxi-daily:run" \
  --http-method POST \
  --oauth-service-account-email ${SCHEDULER_SA}
```

For an initial backfill, run `ingest.py` over the historical months once, then
`dbt build` a single time, before enabling the schedule.
