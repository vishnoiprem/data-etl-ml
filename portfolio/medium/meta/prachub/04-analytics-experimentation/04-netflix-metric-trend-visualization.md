# Visualize a Netflix Streaming Metric Trend

## 1. Simple way to think
- Pick ONE metric that captures whether people are actually watching Netflix — "Daily Active Viewers" (DAV) is the obvious one.
- A trend line alone is boring and easy to misread; you need a baseline (what "normal" looks like) drawn behind it.
- Anomalies aren't always bad — a release-date spike is good; a CDN outage spike in the wrong direction is bad. Context matters.
- The chart must be readable in 3 seconds for an exec, but clickable for an analyst who wants to dig.
- Compare to history: same day last week, same day last year, and a forecast — three lines, one number.
- Decomposition beats aggregation: weekday vs. weekend, region, plan tier. The average hides everything.
- Numbers on dashboards go stale; design for refresh latency so users trust what they see.

## 2. Interview write-up (how to solve it)
**Pick the metric:** Daily Active Viewers (DAV) — a unique user who played ≥ 1 minute of content in a calendar day.

**Primary chart (monitoring):**
- Time-series line, daily granularity, trailing 90 days.
- Three overlay lines: actual DAV, expected DAV (forecast from a 28-day trailing seasonal model), and last-year same-weekday.
- Shaded band for ±2σ expected range. Points outside the band are auto-flagged.
- Annotations on the chart for known events (major releases, holidays, outages).

**Supporting panels:**
- % delta vs. expected — a single KPI tile at the top.
- Small-multiples: same chart faceted by region (NA, EMEA, LATAM, APAC) and by plan tier (Basic, Standard, Premium).
- Decomposition view: trend + weekly seasonality + residual — so you can see if today's number is anomalous *after* you strip the weekday effect.

**Diagnosis view (on click):**
- Funnel: Eligible Devices → App Launch → Play Initiated → First Frame → ≥ 1 min Played → ≥ 60 min Played.
- Cohort heatmap: DAV retention by signup month.
- Content-mix breakdown: % of DAV driven by top 10 titles vs. long tail.

**What to monitor vs. diagnose:** Monitor the headline trend with the forecast band. Diagnose via funnel drop-offs, region splits, and content-mix shifts.

## 3. Best optimized solution
- Use a **Bayesian structural time series** model for the forecast so you can attribute anomalies to specific components (trend shift vs. seasonality vs. event) — this is what Netflix and Facebook actually ship.
- **Validate metric quality:** reconcile DAV against server-side play logs and against billing-eligible sessions; report a known-undercount factor in the dashboard footer.
- **Segmentation strategy:** always show the chart at the global level, with one-click drilldowns by region, plan, device class, and content genre. Pre-compute the top-10 most informative splits so analysts don't waste time on noise.
- **Alerting thresholds:** page if actual DAV sits outside the 95% prediction interval for > 2 hours; lower-severity ticket at 24 hours. Anomaly direction matters: drops are urgent, spikes get investigated within the day.
- **Novelty and bias checks:** exclude launch-day launches from baseline windows (don't pollute "normal" with the previous Marvel show). Apply a holiday calendar per region.
- **Why it's optimal:** combines a forecast-aware trend (so anomalies are detected against *what should have happened*) with decomposition and segmentation, so the same chart answers "is something wrong?" and "what changed?" — a single visual does both jobs.

**Common mistakes:** Plotting raw DAV with no forecast or baseline, so every dip looks like a crisis; using monthly granularity and missing the daily story; not annotating known events (releases, outages), so the team wastes time "discovering" them; computing DAV with different definitions in different dashboards; ignoring timezone normalization (a global "day" hides regional effects).
