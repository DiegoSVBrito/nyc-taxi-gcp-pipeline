"""Load the taxi zone lookup table once as a dimension.

The lookup maps LocationID to borough, zone, and service zone. It is small
(around 265 rows) and static, so it is loaded a single time and joined in the
silver layer to turn numeric zone ids into human-readable locations.
"""

import os
import sys

from google.cloud import bigquery

SOURCE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"

PROJECT = os.environ["GCP_PROJECT"]
DATASET = os.environ.get("BQ_DATASET", "nyc_taxi")
ZONE_TABLE = f"{PROJECT}.{DATASET}.dim_taxi_zone"


def main() -> None:
    client = bigquery.Client(project=PROJECT)
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=True,
    )
    load_job = client.load_table_from_uri(
        SOURCE_URL, ZONE_TABLE, job_config=job_config
    )
    load_job.result()
    table = client.get_table(ZONE_TABLE)
    print(f"Loaded {table.num_rows} zones into {ZONE_TABLE}")


if __name__ == "__main__":
    sys.exit(main())
