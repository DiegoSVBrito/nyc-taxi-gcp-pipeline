-- Are airport runs actually worth it?
--
-- Airport trips pay well per trip, but the driver usually returns with an
-- empty cab. This mart compares airport and non-airport trips on per-trip
-- fare and on the efficiency metrics that account for time. The gap between
-- a high fare per trip and a mediocre rate per minute is the signal a driver
-- needs: a big fare that ties up a long stretch of time, plus a likely empty
-- return, can lose to faster turnover elsewhere.

with trips as (

    select * from {{ ref('int_trips_enriched') }}

)

select
    is_airport_trip,

    count(*)                                    as trip_count,
    round(avg(total_amount), 2)                 as avg_total_per_trip,
    round(avg(trip_distance_miles), 2)          as avg_distance_miles,
    round(avg(trip_duration_min), 1)            as avg_duration_min,
    round(avg(dollars_per_minute), 2)           as avg_dollars_per_minute,
    round(avg(dollars_per_mile), 2)             as avg_dollars_per_mile

from trips
group by is_airport_trip
order by is_airport_trip desc
