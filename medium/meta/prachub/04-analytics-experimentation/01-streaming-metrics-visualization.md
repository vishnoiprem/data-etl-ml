# Design Visualizations for Streaming Metrics

## 1. Simple way to think
- A streaming service sends tiny video packets continuously, and "rebuffering" is when playback stalls because the next chunk didn't arrive in time — like a stutter while watching Netflix.
- Startup time is how long you wait from pressing "Play" until the video actually starts moving.
- Both metrics need two views: a **monitoring** view (is something wrong RIGHT NOW?) and a **diagnosis** view (WHY is it wrong, and for WHOM?).
- Monitoring should be a single, glanceable chart with thresholds; diagnosis should be interactive and let you slice the data many ways.
- Engineers care about percentiles (p50, p95, p99), not averages, because a few bad users can hide behind a good mean.
- Anomaly detection beats eyeballing — you can't stare at 50 charts, so let the system yell when something breaks.
- The right chart for a trend is almost always a time series; tables and pie charts hide trends.

## 2. Interview write-up (how to solve it)
**Pick the metric:** Rebuffer ratio = (total rebuffer duration) / (total play time) per session. Startup time = time from play request to first frame rendered. Report both as p50, p95, p99 with a 5-minute granularity.

**Monitoring dashboard (top-level):**
- Time-series line chart of rebuffer ratio and startup time at p95.
- A traffic-light band (green/yellow/red) drawn from historical baselines (e.g., 1.5x and 2x the trailing 7-day p95).
- Headline number: "% of sessions that experienced a rebuffer."
- An alert if p95 moves > 2σ from baseline for > 10 minutes.

**Diagnosis dashboard (drill-down):**
- Stacked bar by device class, CDN, ASN/ISP, codec, content title, geolocation.
- Heatmap of rebuffer ratio by hour-of-day × day-of-week to surface off-peak issues.
- Funnel: Play Request → Manifest Fetch → First Byte → First Frame → Steady State. Drop-off at each step points to the failing layer.
- A "session explorer" that lists worst sessions and lets you replay events.

**What to monitor vs. diagnose:** Monitor summary statistics and SLOs; diagnose the funnel, segmentation, and per-session events.

## 3. Best optimized solution
- Use **p95/p99 weighted by session count** (not session-mean) so heavy users aren't hidden by lightweight ones; a single whale shouldn't tank the metric.
- Apply **CUSUM or EWMA** control charts for change-point detection — they catch slow drifts a static threshold misses.
- Add **counterfactual baseline** (expected metric given the same traffic mix) so a CDN mix shift doesn't look like a regression.
- Validate quality: cross-check client-reported rebuffer against server-side stall events; reconcile via a calibration factor before publishing the metric.
- Segment deliberately: device, network type (Wi-Fi vs cellular), CDN edge, content bitrate, geo, account tenure. Avoid Simpson's paradox by checking segments don't flip the global trend.
- Alert thresholds: page on-call at p95 > 1.5× baseline for 5 min sustained; ticket at 1.2× for 30 min. Different severities = different pages.
- **Why it's optimal:** separates signal from noise (anomaly detection), actionability (funnel + segmentation), and prevents alert fatigue via tiered thresholds.

**Common mistakes:** Using averages instead of percentiles (hides tail latency); confusing correlation with causation during CDN mix shifts; building one mega-dashboard instead of monitor/diagnose split; alerting on raw values instead of deviation from baseline; not weighting by traffic volume, so a noisy small segment looks as important as a large one.
