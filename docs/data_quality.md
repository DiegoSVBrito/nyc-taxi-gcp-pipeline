# Data quality

The TLC data is real and messy. These are the issues found and how each is
handled. All filtering happens in the staging model so the definition of a
valid trip is in one auditable place.

## Issues found and handling

**Trips with zero or negative duration.** Some rows have a dropoff at or before
the pickup. Dropped: a trip must end after it starts.

**Implausible durations.** A few trips last many hours or a fraction of a
second. Kept only trips between 1 and 720 minutes. The ceiling is twelve hours,
beyond which a single metered trip is not credible.

**Zero or absurd distance.** Trips with zero distance or distances over 200
miles are dropped. Zero distance with a fare usually means a canceled or
mis-metered trip; 200 miles is far beyond any city trip.

**Negative money.** Negative `fare_amount` or `total_amount` appear as
adjustments or errors. Dropped, since a driver's earning analysis should not
include negative billable trips.

**Odd passenger counts.** Values of zero or above eight occur. Kept the row but
bounded the accepted range to 0 through 8; nulls are allowed through because the
field is not central to the earnings question.

**The cash tip gap.** This is the most important quality issue and it is not
fixed by filtering, because the data is technically correct. Cash tips are not
recorded by the meter, so cash trips show near-zero tips. Removing or imputing
them would hide the problem. Instead the gap is surfaced in the
`tipping_by_payment` mart through `pct_trips_with_recorded_tip`, and called out
in the findings so it is read as a recording artifact rather than rider
behavior. The right handling here was documentation, not deletion.

**Unmatched zone ids.** A small number of `LocationID` values do not resolve in
the lookup. The zone join is a left join, so these trips are kept with null
borough and zone, and the zone-level marts filter out null zones rather than
dropping the trips entirely from other analyses.

## Why filter in staging

Putting every rule in the staging model keeps the rest of the pipeline simple:
intermediate and mart models can assume their input is already valid. It also
makes the rules reviewable as code, and the dbt tests on the staging output
confirm the rules held.
