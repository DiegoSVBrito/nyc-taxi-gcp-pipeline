# Container for the daily Cloud Run Job. Holds both the ingestion code and the
# dbt project, kept small to keep cold starts and cost low.

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY ingestion/requirements.txt ingestion/requirements.txt
RUN pip install --no-cache-dir -r ingestion/requirements.txt \
    && pip install --no-cache-dir "dbt-bigquery>=1.8.0"

COPY ingestion/ ingestion/
COPY dbt/ dbt/
COPY orchestration/run_daily.sh run_daily.sh

RUN chmod +x run_daily.sh

ENTRYPOINT ["./run_daily.sh"]
