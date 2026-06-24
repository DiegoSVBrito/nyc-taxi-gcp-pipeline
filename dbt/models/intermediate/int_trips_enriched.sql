-- Enrich clean trips with the metrics the earnings analysis needs.
--
-- This is where raw columns become decision-useful signals: dollars per mile,
-- dollars per minute, tip percentage, the hour and weekday of the pickup, and
-- whether the trip touches an airport. Zone ids are resolved to boroughs and
-- zone names on both ends.

with trips as (

    select * from {{ ref('stg_yellow_taxi') }}

),

pickup_zone as (

    select
        locationid as location_id,
        borough    as pu_borough,
        zone       as pu_zone
    from {{ source('raw', 'dim_taxi_zone') }}

),

dropoff_zone as (

    select
        locationid as location_id,
        borough    as do_borough,
        zone       as do_zone
    from {{ source('raw', 'dim_taxi_zone') }}

),

enriched as (

    select
        trips.*,

        pickup_zone.pu_borough,
        pickup_zone.pu_zone,
        dropoff_zone.do_borough,
        dropoff_zone.do_zone,

        extract(hour from trips.pickup_at)      as pickup_hour,
        format_date('%A', trips.pickup_date)    as pickup_weekday,

        -- earnings efficiency, guarded against divide by zero
        case
            when trips.trip_distance_miles > 0
            then round(trips.total_amount / trips.trip_distance_miles, 2)
        end                                     as dollars_per_mile,

        case
            when trips.trip_duration_min > 0
            then round(trips.total_amount / trips.trip_duration_min, 2)
        end                                     as dollars_per_minute,

        case
            when trips.fare_amount > 0
            then round(trips.tip_amount / trips.fare_amount * 100, 1)
        end                                     as tip_pct,

        -- airport zones: JFK (132), LaGuardia (138), Newark (1)
        -- hardcoded for now — if this model ever needs to support other cities
        -- or the TLC adds a new terminal zone, move these to a seed table
        case
            when trips.pu_location_id in (1, 132, 138)
              or trips.do_location_id in (1, 132, 138)
            then true else false
        end                                     as is_airport_trip,

        case when trips.payment_type = 1 then 'card'
             when trips.payment_type = 2 then 'cash'
             else 'other'
        end                                     as payment_method

    from trips
    left join pickup_zone
        on trips.pu_location_id = pickup_zone.location_id
    left join dropoff_zone
        on trips.do_location_id = dropoff_zone.location_id

)

select * from enriched
