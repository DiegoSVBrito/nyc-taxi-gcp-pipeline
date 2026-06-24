-- How does tipping behave across payment methods?
--
-- The important finding lives here. Card trips record tips; cash trips almost
-- never do, because cash tips are handed over physically and not entered into
-- the meter. A driver reading the raw tip column would wrongly conclude that
-- cash riders do not tip. This mart surfaces that gap explicitly so the
-- conclusion is read correctly: it is a data recording artifact, not behavior.

with trips as (

    select * from {{ ref('int_trips_enriched') }}

)

select
    payment_method,

    count(*)                                    as trip_count,
    round(avg(fare_amount), 2)                  as avg_fare,
    round(avg(tip_amount), 2)                   as avg_tip,
    round(avg(tip_pct), 1)                       as avg_tip_pct,

    -- share of trips with any recorded tip; near zero for cash exposes the gap
    round(
        countif(tip_amount > 0) / count(*) * 100, 1
    )                                           as pct_trips_with_recorded_tip

from trips
group by payment_method
order by trip_count desc
