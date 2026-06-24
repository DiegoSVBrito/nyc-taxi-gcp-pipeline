# Findings: advice to a new driver

These are the conclusions the queries support. Run `queries.sql` against the
gold marts to reproduce the numbers. The exact figures depend on the month
loaded; the patterns below hold across the data and are what a driver should
act on.

## 1. Think in dollars per hour, not dollars per trip

The instinct of a new driver is to chase big fares. The data says to chase the
best rate per working hour instead. A single long trip can pay a large fare
while tying up forty minutes and ending far from the next rider. Several short
trips in a dense zone can earn more over the same forty minutes and keep the
driver where demand is. Query 1 ranks zone and hour combinations by earnings
per hour, which is the number that actually fills a shift.

## 2. The cash tip trap

Cash trips show almost no tips in the data. A driver who trusts the raw number
would start avoiding cash riders. That would be a mistake. Cash tips are handed
over physically and never entered into the meter, so they are invisible to the
dataset, not absent in reality. Query 2 makes this explicit through
`pct_trips_with_recorded_tip`, which sits near zero for cash and high for card.
The real lesson is about the limits of the data: judge tipping by card trips,
and do not read the cash gap as rider behavior.

## 3. Airport runs are a time tradeoff, not free money

Airport pickups carry a high fare per trip, which makes them look like the best
work available. Query 3 reframes them by time. Once duration is counted, the
per-minute rate on airport runs is often unremarkable, and that is before
accounting for the empty return trip that airport drop-offs usually force. The
advice is not to refuse airport work but to treat it as a round trip when
deciding whether it beats staying in a busy zone.

## 4. Short hops can win on rate

Query 4 buckets trips by distance and compares dollars per minute. The base
charge on the meter is spread over less time on short trips, so the shortest
buckets frequently show the strongest per-minute rate. A driver optimizing for
a full shift should not look down on short fares.

## 5. A simple shift window

For a driver who just wants to know when to work rather than where, query 5
collapses zone and ranks hours of the day by earnings per hour. It gives a plain
answer to "what hours should I drive" without the zone detail.

## How to use this

A new driver does not need all five views at once. The practical routine: pick a
shift window from query 5, position in a high rate-per-hour zone from query 1,
take short and medium trips freely, treat airport runs as round trips before
accepting them, and ignore the cash tip column entirely when judging where the
money is.
