-- Short trips or long trips: which earns more per minute?
--
-- Buckets trips by distance and compares the per-minute rate. Short urban
-- hops often beat long hauls on dollars per minute because the meter's base
-- charge is spread over less time, and the driver is free again sooner. This
-- mart lets the driver see the tradeoff between a few large fares and many
-- small ones.

with trips as (

    select * from {{ ref('int_trips_enriched') }}

),

bucketed as (

    select
        *,
        case
            when trip_distance_miles < 1 then '0 to 1 mi'
            when trip_distance_miles < 3 then '1 to 3 mi'
            when trip_distance_miles < 6 then '3 to 6 mi'
            when trip_distance_miles < 12 then '6 to 12 mi'
            else '12 mi and up'
        end as distance_bucket
    from trips

)

select
    distance_bucket,

    count(*)                                    as trip_count,
    round(avg(total_amount), 2)                 as avg_total,
    round(avg(trip_duration_min), 1)            as avg_duration_min,
    round(avg(dollars_per_minute), 2)           as avg_dollars_per_minute,
    round(avg(tip_pct), 1)                       as avg_tip_pct

from bucketed
group by distance_bucket
order by min(trip_distance_miles)
