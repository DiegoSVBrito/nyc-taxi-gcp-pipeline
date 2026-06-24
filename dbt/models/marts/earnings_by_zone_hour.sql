-- Where and when does a driver earn the most per working hour?
--
-- Aggregates total earnings and time worked by pickup zone and hour, then
-- expresses it as dollars per hour. This is the headline view: it answers
-- "where should I be, and at what time" in the currency that matters to a
-- driver, which is earnings per hour rather than per trip.

with trips as (

    select * from {{ ref('int_trips_enriched') }}

)

select
    pu_borough,
    pu_zone,
    pickup_hour,

    count(*)                                    as trip_count,
    round(sum(total_amount), 2)                 as total_earnings,
    round(sum(trip_duration_min) / 60.0, 1)     as hours_worked,

    round(
        sum(total_amount) / nullif(sum(trip_duration_min) / 60.0, 0), 2
    )                                           as earnings_per_hour,

    round(avg(total_amount), 2)                 as avg_fare_per_trip,
    round(avg(trip_distance_miles), 2)          as avg_distance_miles

from trips
where pu_zone is not null
group by pu_borough, pu_zone, pickup_hour
having count(*) >= 50
order by earnings_per_hour desc
