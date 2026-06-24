# Data model

The pipeline follows a medallion pattern with three layers. Each layer has one
job, and data only ever flows forward.

## Bronze: raw

`bronze_yellow_taxi` holds the trips exactly as the TLC source provides them,
one row per trip. It is partitioned by `tpep_pickup_datetime` (day). Nothing is
cleaned or reshaped here. Keeping a faithful raw copy means any bug in later
logic can be fixed by rebuilding from bronze without re-downloading the source.

`dim_taxi_zone` is the static lookup of `LocationID` to borough and zone, loaded
once.

## Silver: cleaned and enriched

`stg_yellow_taxi` casts types and removes rows that cannot represent a real
billable trip (see `data_quality.md`). It is incremental and partitioned by
`pickup_date`, clustered by `pu_location_id`.

`int_trips_enriched` joins the zone dimension on both pickup and dropoff, and
derives the analysis metrics: `dollars_per_mile`, `dollars_per_minute`,
`tip_pct`, `pickup_hour`, `pickup_weekday`, `is_airport_trip`, and a readable
`payment_method`.

## Gold: analytical marts

Four small pre-aggregated tables, each answering one part of the earnings
question:

| Mart | Question |
| --- | --- |
| `earnings_by_zone_hour` | Where and when is the rate per hour highest? |
| `tipping_by_payment` | How does tipping differ by payment method? |
| `airport_runs` | Are airport trips worth the time? |
| `trip_efficiency` | Short trips or long trips per minute? |

Because the marts are small and pre-aggregated, the driver-facing queries scan
almost nothing and cost effectively zero.

## Schema of stg_yellow_taxi

| Column | Type | Notes |
| --- | --- | --- |
| pickup_date | date | Partition key |
| pickup_at | timestamp | |
| dropoff_at | timestamp | |
| passenger_count | int64 | |
| trip_distance_miles | float64 | |
| pu_location_id | int64 | Joins to dim_taxi_zone |
| do_location_id | int64 | Joins to dim_taxi_zone |
| payment_type | int64 | TLC code |
| fare_amount | float64 | |
| tip_amount | float64 | |
| tolls_amount | float64 | |
| total_amount | float64 | |
| trip_duration_min | float64 | Derived |
