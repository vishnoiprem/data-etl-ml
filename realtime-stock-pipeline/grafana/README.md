# Grafana — provisioned dashboards and datasource

> **The Grafana provisioning layer for the realtime stock pipeline.**
> Two config files: `provisioning/datasources/timescaledb.yaml`
> auto-registers the TimescaleDB datasource on container start;
> `provisioning/dashboards/dashboards.yaml` tells Grafana where
> to load dashboard JSONs from disk.

The Grafana container comes up with the TimescaleDB datasource
already wired and the dashboards already mounted. You do not
have to click "Add data source" or "Import dashboard" in the
UI. That's the whole point of the `provisioning/` directory.

---

## Files

```
grafana/
└── provisioning/
    ├── datasources/
    │   └── timescaledb.yaml   # auto-registers the TimescaleDB datasource
    └── dashboards/
        ├── dashboards.yaml    # tells Grafana where to find dashboards
        └── <your-dashboards>.json
```

The split is by Grafana's own convention: datasources and
dashboards are provisioned separately, and dashboards are loaded
from a directory you mount into the container at
`/var/lib/grafana/dashboards`.

---

## The datasource

`datasources/timescaledb.yaml` registers a Postgres datasource
named `TimescaleDB` pointing at the `timescaledb` container, with
the `timescaledb: true` flag set so Grafana's Postgres
datasource shows the hypertable-aware UI.

```yaml
apiVersion: 1

datasources:
  - name: TimescaleDB
    type: postgres
    access: proxy
    url: timescaledb:5432
    database: stocks
    user: stocks
    isDefault: true
    jsonData:
      maxOpenConns: 10
      sslmode: disable
      postgresVersion: 1500
      timescaledb: true
```

`isDefault: true` means every new panel you add in the UI
defaults to this datasource. The credentials (`stocks` /
`stocks`) are the dev defaults; production should use
Grafana's secret store or environment-variable interpolation.

---

## The dashboard provider

`dashboards/dashboards.yaml` tells Grafana to load dashboards
from `/var/lib/grafana/dashboards` and re-scan every 30 seconds
so adding a new dashboard JSON doesn't require a container
restart.

```yaml
apiVersion: 1

providers:
  - name: default
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

`foldersFromFilesStructure: true` means a subdirectory under
`dashboards/` becomes a Grafana folder. Useful when you have
many dashboards and want them grouped by topic.

---

## What dashboards you get

The shipped dashboard set covers the four panels the human looks
at during a trading day:

| Dashboard | What it shows |
|-----------|---------------|
| **Live Prices** | Latest price per ticker, day change %, intraday range, volume — refreshed every 5s |
| **AI Signals** | Latest signal per ticker (WATCH / HOLD / SELL), model name, confidence — refreshed every 60s |
| **Intraday Movers** | Top N tickers by abs(change %) since market open, with sparklines |
| **Model Accuracy** | Per-model, per-ticker hit rate over the last N signals — refreshed hourly |

Each dashboard is one JSON file under `provisioning/dashboards/`.
Edit a panel, save, the file updates on disk, Grafana reloads
within 30s.

---

## How to add a new dashboard

1. Create a new JSON file under
   `provisioning/dashboards/<your-name>.json`. (Or use the
   Grafana UI to author it, then "Export → Save to file" and
   move the file into the provisioning directory.)
2. Restart Grafana (or wait 30s for the provider to re-scan).
3. The dashboard appears in the default folder.

If you want it in a sub-folder, put it under
`provisioning/dashboards/<folder-name>/<your-dashboard>.json`
and the folder will be created on load.

---

## What this is NOT

- **Not a metrics store.** Grafana here is a viewer over
  TimescaleDB. For metrics (Flink lag, Kafka consumer lag, JVM
  heap), use Prometheus + a separate Grafana stack. Mixing
  metrics and business data in one Grafana is a common mistake.
- **Not the alerting layer.** Grafana alerting can be configured
  here, but the strategy's alerts (BUY / SELL / PANIC) live in
  the [`../trade-finder/`](../trade-finder/) process and the
  Telegram bot. The dashboards are for humans; the alerts are
  for the system.
- **Not auth.** The dev compose file runs Grafana without auth.
  Production needs at least basic auth, and ideally OAuth /
  SAML against your identity provider. The provisioning files
  here are the dev defaults.

---

## Related directories

- [`../`](../) — the parent `realtime-stock-pipeline/`. Start
  there for the full architecture.
- [`../db/`](../db/) — the TimescaleDB schema and views that
  these dashboards query.
- [`../flink/`](../flink/) — the Flink jobs that populate the
  tables the dashboards read from.
- [`../ai_signals/`](../ai_signals/) — the ML signal layer
  that the AI Signals dashboard shows.
