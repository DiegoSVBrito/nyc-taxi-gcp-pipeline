# Orchestration

The daily pipeline runs as a Cloud Run Job triggered by Cloud Scheduler.
Simple setup — one cron, one container. Composer was the other option but
it keeps an environment running 24/7 regardless of how often your DAG fires,
and the base cost (~$300/mo) is hard to justify for a single daily trigger.

One thing to know: the `run_daily.sh` script loads the month two months back
by default, because TLC data typically lags by 4-6 weeks. You can override
this with the `TARGET_MONTH` env var for backfills.

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
