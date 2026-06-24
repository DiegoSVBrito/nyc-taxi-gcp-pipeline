-- Standalone analytical queries for the driver earnings question.
--
-- These run directly against the gold marts in the BigQuery console. They are
-- the same logic the marts expose, written as ready-to-run queries so the
-- findings can be reproduced without dbt.

-- 1. Top 15 zone and hour combinations by earnings per working hour.
--    Answers: where should the driver be, and when?
--    Note: the having clause (count >= 50) filters out zone-hour pairs with too few
--    trips to be reliable. I tried lower thresholds and got some odd outliers —
--    a single $200 trip at 3am in an obscure zone skewing the average badly.
select
    pu_borough,
    pu_zone,
    pickup_hour,
    trip_count,
    earnings_per_hour,
    avg_fare_per_trip
from `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`
order by earnings_per_hour desc
limit 15;

-- 2. Tipping by payment method.
--    Answers: do cash riders really tip less? (No, the data just does not
--    record cash tips. Watch pct_trips_with_recorded_tip for cash.)
select
    payment_method,
    trip_count,
    avg_fare,
    avg_tip,
    avg_tip_pct,
    pct_trips_with_recorded_tip
from `massive-network-500412-u2.nyc_taxi.tipping_by_payment`
order by trip_count desc;

-- 3. Airport runs versus everything else.
--    Answers: is the high airport fare worth the time and empty return?
select
    is_airport_trip,
    trip_count,
    avg_total_per_trip,
    avg_duration_min,
    avg_dollars_per_minute
from `massive-network-500412-u2.nyc_taxi.airport_runs`
order by is_airport_trip desc;

-- 4. Short versus long trips on dollars per minute.
--    Answers: many small fares or a few big ones?
select
    distance_bucket,
    trip_count,
    avg_total,
    avg_duration_min,
    avg_dollars_per_minute
from `massive-network-500412-u2.nyc_taxi.trip_efficiency`
order by avg_dollars_per_minute desc;

-- 5. Best hours of the day overall, collapsing zone.
--    A simpler companion to query 1 for a driver who just wants a shift window.
select
    pickup_hour,
    sum(trip_count)                                              as trips,
    round(sum(total_earnings) / nullif(sum(hours_worked), 0), 2) as earnings_per_hour
from `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`
group by pickup_hour
order by earnings_per_hour desc;
