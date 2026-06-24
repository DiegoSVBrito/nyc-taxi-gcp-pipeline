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
| Storage and compute | BigQuery | Serverless and columnar — scales to petabytes without cluster management, and partitioning keeps query costs flat as history grows. Free tier covers most of the current workload as a side effect. |
| Landing zone | Cloud Storage | Cheap durable staging for the raw Parquet before load. |
| Ingestion | BigQuery load jobs | Batch loads from GCS are free. They do not consume slots or the 1 TB query allowance. |
| Transformation | dbt on BigQuery | All compute stays inside BigQuery. dbt adds lineage, tests, and native incremental models. No external engine. |
| Orchestration | Cloud Scheduler + Cloud Run Job | Pennies per month. A daily cron triggers a short container run. |

### What was deliberately avoided

Dataflow and Dataproc were the obvious first candidates and I spent some time
looking at both. The problem is that they bill for workers by the hour. A daily
job processing one new month — roughly 3 million rows — would spin up a cluster,
finish in a few minutes, and leave compute running for a workload that BigQuery
handles for free as a load job. The math does not work at this scale.

Cloud Composer was the other temptation. It is the "proper" orchestration answer
and I use it at work for larger pipelines. But its environment runs continuously
regardless of how often your DAG fires, and the base cost is around 300 USD per
month before you run a single task. For one daily trigger, Cloud Scheduler and
a Cloud Run Job do the same job for pennies. Composer would be the right call
if this pipeline grew to dozens of interdependent DAGs — not for this.

## Architecture

Three layers — bronze keeps the raw source intact, silver cleans and enriches, gold aggregates for the earnings analysis.

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

The pipeline does not reprocess old data. On ingestion, any existing rows for
the target month are cleared before the new load — so re-running a month is
safe and produces no duplicates. On the dbt side, the silver model uses
`insert_overwrite` on the `pickup_date` partition, which means a daily run
only touches partitions for data that actually changed. Old months are left
alone.

This matters more as history grows. Running month 60 should cost the same as
running month 2, and with this setup it does.

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

Prerequisites: a GCP project with billing enabled and `gcloud` installed.

### Quick start

On macOS or Linux:

```bash
cp .env.example .env        # GCP_PROJECT is already set — update if yours differs
source .env
./setup.sh 2023-01
```

On Windows PowerShell:

```powershell
.\setup.ps1 -Month 2023-01
```

Both scripts check for existing resources before creating, so re-running is safe.

### Manual steps

If you prefer to run each stage yourself:

```bash
source .env

python ingestion/load_zones.py          # once
python ingestion/ingest.py --month 2023-01
cd dbt && dbt build
```

Detailed setup and the production scheduling notes live in
`docs/pipeline_design.md`.

## Findings

The full analysis is in `analysis/README.md`. A few things that stood out:

- Flushing Meadows-Corona Park in Queens dominates the top zone-hour rankings,
  returning over $260/hr at peak evening hours. I did not expect a Queens zone
  to beat Midtown this consistently — it is driven by event venues, not general
  density.
- The cash tip column reads zero for 513,185 trips. That is not rider behavior,
  it is a recording gap: cash tips never touch the meter. A driver who acts on
  that number is optimizing against a data artifact.
- Short trips under one mile return $2.88 per minute — the highest rate in the
  dataset, better than long trips and better than airport runs once wait time
  is counted. This one surprised me most.
