# NYC Yellow Taxi Analytics on GCP

A cost-optimized data pipeline that ingests NYC Yellow Taxi trip data, cleans
and enriches it, and produces analytical queries that answer one question:
**if you were advising a new taxi driver, how should they maximize earnings?**

The pipeline is built to process one month of data today and scale to five
years of monthly data running daily, without reprocessing what it has already
loaded.

## Why this stack

The dataset is smaller than it looks. Five years of Yellow Taxi trips is roughly
180 million rows, which compresses to a few gigabytes of Parquet. That is small
by BigQuery standards, and it drives every decision below.

| Concern | Choice | Reason |
| --- | --- | --- |
| Storage and compute | BigQuery | Serverless, no cluster to keep running, generous free tier (1 TB query/month, 10 GB storage). |
| Landing zone | Cloud Storage | Cheap durable staging for the raw Parquet before load. |
| Ingestion | BigQuery load jobs | Batch loads from GCS are free. They do not consume slots or the 1 TB query allowance. |
| Transformation | dbt on BigQuery | All compute stays inside BigQuery. dbt adds lineage, tests, and native incremental models. No external engine. |
| Orchestration | Cloud Scheduler + Cloud Run Job | Pennies per month. A daily cron triggers a short container run. |

### What was deliberately avoided

Dataflow and Dataproc were considered and rejected. They bill for workers by the
hour, and a daily job processing only one new month (around 3 million rows) would
leave compute running for a workload that BigQuery handles in seconds for free.
Cloud Composer was also rejected for the same reason: its environment runs
continuously and costs roughly 300 USD per month on its own, which is not
justified for a single daily trigger.

## Architecture

The data flows through three layers, following a medallion pattern.

```
TLC source (Parquet, monthly)
        |
        v
  GCS landing bucket  (year=YYYY/month=MM/)
        |
        v  BigQuery load job (free)
        |
   BRONZE  raw, partitioned by pickup_date, 1:1 with source
        |
        v  dbt incremental
   SILVER  cleaned and enriched: zone joins, $/mile, $/min, tip_pct, airport flags
        |
        v  dbt
   GOLD    pre-aggregated marts that answer the earnings question
```

See `docs/data_model.md` for the full layer and schema description.

## Incremental design

The pipeline never reprocesses old data. Two mechanisms guarantee this:

1. **Ingestion is idempotent per month.** Before loading a month, the loader
   removes any existing rows for that month's partition, then appends. Running
   the same month twice produces the same result, never duplicates.
2. **Transformations are incremental.** The silver model uses dbt's
   `insert_overwrite` strategy on the `pickup_date` partition. A daily run only
   touches the partitions for newly arrived data. Old partitions are left
   untouched, which keeps both cost and runtime flat as history grows.

## Rough monthly cost in production (5 years, daily runs)

| Item | Estimate |
| --- | --- |
| BigQuery storage (~12-15 GB, partitioned) | ~0.30 USD |
| Ingestion (load jobs) | 0.00 USD (free) |
| GCS landing (few GB, lifecycle to delete after load) | ~0.10 USD |
| Daily transformation (processes only the new partition) | < 1.00 USD |
| Cloud Scheduler + Cloud Run Job | ~0.00-0.50 USD |
| **Total** | **~1-3 USD / month** |

For contrast, the same daily pipeline on Dataflow would cost tens of dollars per
month in idle and per-run worker time, and adding Cloud Composer would add around
300 USD per month for the environment alone. The point of this design is that the
workload does not need either.

## Repository layout

```
nyc-yellow-taxi-gcp/
  ingestion/        download source, stage to GCS, load to BigQuery (bronze)
  dbt/              staging, intermediate, and mart models (silver, gold)
  analysis/         standalone analytical queries with documented findings
  docs/             data model, pipeline design, data quality notes
  orchestration/    Cloud Run / Scheduler entrypoint for daily runs
```

## How to run

Prerequisites: a GCP project with BigQuery and Cloud Storage enabled, and
`gcloud` authenticated locally.

```bash
# 1. Set your project and create the landing bucket + dataset
export GCP_PROJECT="your-project-id"
export GCS_BUCKET="nyc-taxi-landing-${GCP_PROJECT}"
export BQ_DATASET="nyc_taxi"

# 2. Ingest one month (idempotent, safe to re-run)
python ingestion/ingest.py --month 2023-01

# 3. Load the zone lookup dimension once
python ingestion/load_zones.py

# 4. Build the models
cd dbt && dbt build
```

Detailed setup and the production scheduling notes live in
`docs/pipeline_design.md`.

## Findings

The full advice to the driver, backed by query results, is in
`analysis/README.md`. The headline insights:

- Earnings per working hour matter more than earnings per trip. A long airport
  run can pay less per hour than fast turnover in a dense zone once the empty
  return trip is counted.
- Cash trips appear to tip almost nothing. This is a reporting artifact, not
  driver behavior: cash tips are not recorded in the system. Reading the raw
  number would mislead a driver into avoiding cash riders.
- Airport pickups pay well per trip but the dead-heading return depresses the
  hourly rate. The runs are worth modeling as a round trip, not a single leg.
