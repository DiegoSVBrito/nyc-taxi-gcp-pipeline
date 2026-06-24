# Findings: advice to a new driver

Numbers below are from the January 2023 data (3,066,766 trips after cleaning).
Run `queries.sql` against the gold marts to reproduce them.

## 1. Think in dollars per hour, not dollars per trip

This reframe is the most useful thing I got out of the analysis. The instinct
is to chase big fares — airport runs, long crosstown trips. But when you rank
zone-hour combinations by earnings per working hour, a different picture shows
up.

The top of the list is almost entirely Flushing Meadows-Corona Park in Queens,
evening hours. Hour 23 there returns $262.75 per hour across 98 trips. That is
not a fluke — the zone sits next to Citi Field and the USTA tennis center, and
event traffic drives consistent demand from 19h onward. A driver who knows to
be there at 10pm on a weeknight will earn more per hour than one chasing the
occasional $70 airport fare.

The per-hour framing also catches something the per-trip average hides: a long
trip that ends in a dead zone has a hidden cost. You stop earning the moment you
drop off, and if the next pickup is twenty minutes away, the clock was running
against you.

## 2. The cash tip trap

When I first looked at the tipping query, cash trips showed $0.00 average tip
across 513,185 rides. That felt too clean to be real. It is.

Cash tips are physically handed to the driver and never entered into the meter,
so the TLC system simply does not see them. The `pct_trips_with_recorded_tip`
column makes this obvious: 96% of card trips have a recorded tip, 0% of cash
trips do. The fares are nearly identical ($18.51 for cash vs $18.47 for card),
so there is no evidence that cash riders are worse customers — just that their
tips are invisible to the dataset.

A driver who reads the raw average and starts steering toward card riders only
is optimizing against a recording gap, not reality.

## 3. Airport runs: better than average, not as good as they look

Airport trips average $74.54 with a $2.51 per-minute rate, versus $21.95 and
$2.07 for everything else. That premium is real. But it only counts the trip in.

Most airport drop-offs end in a holding queue or an empty return to the city.
Neither of those minutes earns anything, and the data does not capture them.
If the queue at JFK is forty minutes, the effective per-minute rate on that
$75 trip drops closer to the city average once you account for the dead time.

The question before accepting an airport run is not "is $74 a good fare" but
"what does the next hour look like after I drop off." If the queue is short and
there is pickup demand near the airport, it is worth it. If not, staying in a
dense zone is probably better.

## 4. Short trips pay better per minute than long ones

This one surprised me. Trips under one mile return $2.88 per minute on average.
The 1-3 mile bucket — the most common, with 1.4 million trips — returns $1.88.
The 3-6 mile bucket is last at $1.68.

The mechanism is simple: the base fare and minimum charge are spread over less
time on a short trip, so the meter starts at a high effective rate and the ride
ends before the per-mile rate has time to pull it down. A driver who refuses
short fares to hold out for longer ones is giving up the most efficient part
of the rate structure.

## 5. When to drive

If location is fixed, the hours matter a lot. The top of the hour ranking:

| Hour | $/hr |
| --- | --- |
| 5am | $155.53 |
| 4am | $142.58 |
| 3am | $130.17 |
| 11pm | $128.89 |
| 6am | $128.39 |

Early morning is not high-volume but competition is low and the trips that do
come — airport runs, late-shift workers, bar close — tend to pay well. The
19-23h window has much higher volume at only slightly lower rates, so it is
probably the better choice for a full shift. Midday (11am-4pm) is consistently
the weakest window.

## What I'd do with more time

The zone-hour mart covers January. I would want to see whether Flushing Meadows
is consistently at the top or whether it is driven by a specific event in that
month. The USTA Open is in August-September, Citi Field has a full baseball
season — the rankings likely shift across months and I would not tell a driver
to camp there year-round without checking a few more months of data first.
