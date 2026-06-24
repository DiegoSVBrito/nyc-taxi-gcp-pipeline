"""Load the taxi zone lookup table once as a dimension.

The lookup maps LocationID to borough, zone, and service zone. It is small
(around 265 rows) and static, so it is loaded a single time and joined in the
silver layer to turn numeric zone ids into human-readable locations.

BigQuery load jobs cannot read directly from an https URL, so the CSV is staged
in the same GCS landing bucket as the trip data before being loaded. This keeps
all raw/landing bytes in one durable place and matches the bronze ingest path.
"""

import os
import sys
import tempfile

import requests
from google.cloud import bigquery, storage

SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
GCS_OBJECT = "dimensions/taxi_zone_lookup.csv"

PROJECT = os.environ["GCP_PROJECT"]
BUCKET = os.environ["GCS_BUCKET"]
DATASET = os.environ.get("BQ_DATASET", "nyc_taxi")
ZONE_TABLE = f"{PROJECT}.{DATASET}.dim_taxi_zone"


def download(local_path: str) -> None:
    print(f"Downloading {SOURCE_URL}")
    response = requests.get(SOURCE_URL, timeout=60)
    response.raise_for_status()
    with open(local_path, "wb") as handle:
        handle.write(response.content)
    print(f"Saved to {local_path}")


def stage_to_gcs(local_path: str) -> str:
    client = storage.Client(project=PROJECT)
    bucket = client.bucket(BUCKET)
    blob = bucket.blob(GCS_OBJECT)
    blob.upload_from_filename(local_path)
    gcs_uri = f"gs://{BUCKET}/{GCS_OBJECT}"
    print(f"Staged to {gcs_uri}")
    return gcs_uri


def main() -> None:
    client = bigquery.Client(project=PROJECT)

    local_path = os.path.join(tempfile.gettempdir(), "taxi_zone_lookup.csv")
    download(local_path)
    gcs_uri = stage_to_gcs(local_path)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    load_job = client.load_table_from_uri(gcs_uri, ZONE_TABLE, job_config=job_config)
    load_job.result()

    os.remove(local_path)
    table = client.get_table(ZONE_TABLE)
    print(f"Loaded {table.num_rows} zones into {ZONE_TABLE}")


if __name__ == "__main__":
    sys.exit(main())
