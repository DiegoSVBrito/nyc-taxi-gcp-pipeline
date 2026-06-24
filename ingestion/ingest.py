"""Ingest one month of NYC Yellow Taxi data into BigQuery.

Downloads the monthly Parquet from the TLC source, stages it in GCS, then
loads it into the bronze table with a BigQuery load job (which is free and
does not count against the 1 TB query allowance).

Clears the month's partition before loading so re-runs don't duplicate rows.
"""

import argparse
import os
import sys
import tempfile
from datetime import datetime

import requests
from google.cloud import bigquery, storage

SOURCE_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_{month}.parquet"
)

PROJECT = os.environ["GCP_PROJECT"]
BUCKET = os.environ["GCS_BUCKET"]
DATASET = os.environ.get("BQ_DATASET", "nyc_taxi")
BRONZE_TABLE = f"{PROJECT}.{DATASET}.bronze_yellow_taxi"


def validate_month(month: str) -> str:
    """Confirm the month argument is in YYYY-MM form and not in the future."""
    try:
        parsed = datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise SystemExit(f"Invalid --month '{month}'. Expected YYYY-MM.")
    if parsed > datetime.now():
        raise SystemExit(f"Month '{month}' is in the future.")
    return month


def download(month: str, local_path: str) -> None:
    url = SOURCE_URL.format(month=month)
    print(f"Downloading {url}")
    # TODO: add a progress indicator here — the January file is ~50 MB and
    # the download just hangs silently, which is confusing the first time you run it.
    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()
        with open(local_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=8 * 1024 * 1024):
                handle.write(chunk)
    print(f"Saved to {local_path}")


def stage_to_gcs(month: str, local_path: str) -> str:
    year, mm = month.split("-")
    blob_name = f"yellow/year={year}/month={mm}/yellow_tripdata_{month}.parquet"
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    gcs_uri = f"gs://{BUCKET}/{blob_name}"
    print(f"Staged to {gcs_uri}")
    return gcs_uri


def clear_partition(client: bigquery.Client, month: str) -> None:
    """Remove existing rows for the month so the load stays idempotent.

    Guarded so the first ever run (table does not exist yet) does not fail.
    """
    query = f"""
        DELETE FROM `{BRONZE_TABLE}`
        WHERE DATE_TRUNC(DATE(tpep_pickup_datetime), MONTH) = DATE('{month}-01')
    """
    try:
        client.query(query).result()
        print(f"Cleared any existing rows for {month}")
    except Exception as error:  # noqa: BLE001 - table may not exist on first run
        if "Not found" in str(error):
            print("Bronze table does not exist yet; nothing to clear.")
        else:
            raise


def load_to_bronze(client: bigquery.Client, gcs_uri: str) -> None:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="tpep_pickup_datetime",
        ),
    )
    load_job = client.load_table_from_uri(
        gcs_uri, BRONZE_TABLE, job_config=job_config
    )
    load_job.result()
    table = client.get_table(BRONZE_TABLE)
    print(f"Loaded into {BRONZE_TABLE}. Total rows now: {table.num_rows}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest one month of taxi data.")
    parser.add_argument("--month", required=True, help="Month as YYYY-MM.")
    args = parser.parse_args()

    month = validate_month(args.month)
    # Use the OS temp dir so this works on Windows as well as Linux/macOS.
    local_path = os.path.join(
        tempfile.gettempdir(), f"yellow_tripdata_{month}.parquet"
    )

    download(month, local_path)
    gcs_uri = stage_to_gcs(month, local_path)

    client = bigquery.Client(project=PROJECT)
    clear_partition(client, month)
    load_to_bronze(client, gcs_uri)

    os.remove(local_path)
    print(f"Done. Month {month} ingested.")


if __name__ == "__main__":
    sys.exit(main())
