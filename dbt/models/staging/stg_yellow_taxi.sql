{{
    config(
        materialized="incremental",
        incremental_strategy="insert_overwrite",
        partition_by={
            "field": "pickup_date",
            "data_type": "date",
            "granularity": "day",
        },
        cluster_by=["pu_location_id"],
    )
}}

-- Clean and type the raw trips. This is the first place data quality is
-- enforced. Anything that cannot represent a real, billable trip is filtered
-- out here so downstream models can trust the rows.
--
-- The model is incremental: on a normal run it only reads partitions newer
-- than what is already built, and insert_overwrite rewrites just those
-- partitions. Old data is never touched.

with source as (

    select * from {{ source('raw', 'bronze_yellow_taxi') }}

    {% if is_incremental() %}
        where date(tpep_pickup_datetime) > (
            select coalesce(max(pickup_date), date('1900-01-01'))
            from {{ this }}
        )
    {% endif %}

),

cleaned as (

    select
        date(tpep_pickup_datetime)                       as pickup_date,
        tpep_pickup_datetime                             as pickup_at,
        tpep_dropoff_datetime                            as dropoff_at,
        cast(passenger_count as int64)                   as passenger_count,
        trip_distance                                    as trip_distance_miles,
        cast(pulocationid as int64)                      as pu_location_id,
        cast(dolocationid as int64)                      as do_location_id,
        cast(payment_type as int64)                      as payment_type,
        fare_amount,
        tip_amount,
        tolls_amount,
        total_amount,

        timestamp_diff(
            tpep_dropoff_datetime, tpep_pickup_datetime, second
        ) / 60.0                                         as trip_duration_min

    from source

    where
        -- drop trips that cannot be real
        tpep_dropoff_datetime > tpep_pickup_datetime
        and timestamp_diff(
            tpep_dropoff_datetime, tpep_pickup_datetime, minute
        ) between 1 and 720
        and trip_distance > 0
        and trip_distance < 200
        and fare_amount >= 0
        and total_amount >= 0
        -- keep only plausible passenger counts
        and (passenger_count is null or passenger_count between 0 and 8)
        -- drop trips whose payment type is not a real TLC code (1-6). A value of
        -- 0 is a meter/recording error; keeping it would trip the accepted_values
        -- test and cannot map to a real payment method downstream.
        and payment_type between 1 and 6

)

select * from cleaned
