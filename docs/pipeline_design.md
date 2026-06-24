# Pipeline design

## How it works

A daily run does three things:

1. Ingest the latest month's Parquet from the TLC source into the bronze table,
   via a Cloud Storage staging step and a free BigQuery load job.
2. Run `dbt build`, which rebuilds only the new partitions in silver and
   refreshes the gold marts.
3. Tests run as part of `dbt build`. A failing test fails the run.

In production this is triggered by Cloud Scheduler on a cron, which invokes a
Cloud Run Job running the container in `orchestration/`. The container holds
both the ingestion code and the dbt project.

## What makes it robust

**Idempotency.** Ingestion clears a month's partition before appending, so a
retry or a duplicate trigger cannot create duplicate rows. The silver model uses
`insert_overwrite`, which rewrites whole partitions rather than appending, so a
re-run of a day is also safe.

**Incremental by partition.** Both ingestion and transformation work one
partition at a time. Adding the 60th month costs the same as adding the 2nd. Cost
and runtime stay flat as five years of history accumulate.

**Raw is preserved.** Bronze keeps the source untouched. Any logic bug in silver
or gold is fixed by rebuilding downstream from bronze, with no need to re-fetch
data.

**Tests gate the run.** Null keys, unexpected payment codes, and missing key
metrics fail the build before bad data reaches the marts.

**Quality filtering is explicit and in one place.** The rules that drop
impossible trips live in the staging model and are documented in
`data_quality.md`, so the definition of a valid trip is auditable.

## Running it

Locally, for backfill or development:

```bash
export GCP_PROJECT="massive-network-500412-u2"
export GCS_BUCKET="nyc-taxi-landing-massive-network-500412-u2"
export BQ_DATASET="nyc_taxi"

python ingestion/load_zones.py          # once
python ingestion/ingest.py --month 2023-01
cd dbt && dbt build
```

To backfill a range, loop the ingest call over the months, then run `dbt build`
once at the end.

## Scheduling notes

- Cloud Scheduler: one daily cron job. First three jobs per month are free.
- Cloud Run Job: billed only for the seconds it runs. A single month load plus
  an incremental dbt build is short.
- The job derives the month to load from the run date, so no manual parameter
  is needed in the scheduled path. The `--month` flag stays available for
  backfills and reruns.

## Limitations and what I would do differently

The orchestration here is intentionally minimal — one cron, one container, no
retry logic beyond what Cloud Run provides by default. For a real production
pipeline I would want proper alerting (a Slack or PagerDuty hook on job
failure), a more explicit backfill interface, and probably a lightweight
orchestrator like Prefect or Dagster once the number of steps grows past three
or four. Cloud Composer would be overkill at this scale but Prefect Cloud's
free tier would not add meaningful cost.

The zone dimension is also loaded once and treated as static. In practice the
TLC does update the zone lookup occasionally — new zones appear, names change.
A more complete pipeline would version the dimension or at least check for
updates periodically instead of assuming the CSV from the initial load is
current.
