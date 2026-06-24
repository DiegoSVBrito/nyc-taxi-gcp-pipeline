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

Project: `massive-network-500412-u2`, region: `us-central1`.

```bash
# Build and push the image
gcloud builds submit \
  --tag gcr.io/massive-network-500412-u2/nyc-taxi-daily \
  orchestration/

# Create the Cloud Run Job
gcloud run jobs create nyc-taxi-daily \
  --image gcr.io/massive-network-500412-u2/nyc-taxi-daily \
  --region us-central1 \
  --set-env-vars GCP_PROJECT=massive-network-500412-u2,\
GCS_BUCKET=nyc-taxi-landing-massive-network-500412-u2,\
BQ_DATASET=nyc_taxi

# Schedule it daily at 6am UTC
# Replace SCHEDULER_SA with the service account you create for the scheduler
gcloud scheduler jobs create http nyc-taxi-daily-trigger \
  --schedule "0 6 * * *" \
  --location us-central1 \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/massive-network-500412-u2/jobs/nyc-taxi-daily:run" \
  --http-method POST \
  --oauth-service-account-email SCHEDULER_SA@massive-network-500412-u2.iam.gserviceaccount.com
```

For an initial backfill, loop `ingest.py` over the historical months first, then
run `dbt build` once at the end before enabling the schedule.
