# Makro Data Service Platform — Apache Superset

> The NIQ/LAZADA sales analytics platform rebuilt in Apache Superset,
> connected to Databricks with user-level row-level security.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌─────────────┐  │
│  │  Superset UI │   │ Celery Worker│   │ Celery Beat │  │
│  │  :8088       │   │ (async SQL)  │   │ (scheduler) │  │
│  └──────┬───────┘   └──────┬───────┘   └──────┬──────┘  │
│         │                  │                   │        │
│  ┌──────▼───────┐   ┌──────▼───────────────────▼──────┐ │
│  │  PostgreSQL  │   │           Redis                 │ │
│  │  (metadata)  │   │   (cache + Celery broker)       │ │
│  └──────────────┘   └─────────────────────────────────┘ │
└────────────────────────────┬────────────────────────────┘
                             │ JDBC / HTTP
                    ┌────────▼────────┐
                    │   Databricks    │
                    │  SQL Warehouse  │
                    │  testdb.*       │
                    └─────────────────┘
```

## Three Dashboards

| Dashboard                           | Slug                      | Mirrors Streamlit Page     |
|-------------------------------------|---------------------------|----------------------------|
| Homepage — Sales Growth Influencers | `makro-homepage`          | Home                       |
| Sales Performance Insights          | `makro-sales-performance` | Sales Performance Insights |
| Data Exporter                       | `makro-data-exporter`     | Data Exporter              |

---

## Quick Start

### 1. Prerequisites

- Docker Desktop 4.x+ (or Docker Engine + Compose plugin)
- Access to a Databricks workspace with a SQL Warehouse
- A Databricks Personal Access Token (PAT)

### 2. Clone the repo

```bash
git clone https://github.com/vishnoiprem/data-etl-ml/
cd makro-superset
```

### 3. Configure environment

```bash
cp .env .env
```

Edit `.env` and fill in:

| Variable               | Description                   | Example                                                    |
|------------------------|-------------------------------|------------------------------------------------------------|
| `SUPERSET_SECRET_KEY`  | Random hex string (32+ chars) | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ADMIN_PASSWORD`       | Superset admin login password | `Makro@2026!`                                              |
| `POSTGRES_PASSWORD`    | Internal PostgreSQL password  | any strong password                                        |
| `DATABRICKS_HOST`      | Workspace hostname            | `adb-123456.12.azuredatabricks.net`                        |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse path            | `/sql/1.0/warehouses/abc123`                               |
| `DATABRICKS_TOKEN`     | Personal access token         | `dapi_xxxx`                                                |
| `DATABRICKS_SCHEMA`    | Default schema                | `testdb`                                                   |

#### Where to find Databricks settings

1. Open your Databricks workspace
2. Go to **SQL Warehouses** → select your warehouse
3. Click **Connection details** tab
4. Copy **Server hostname** → `DATABRICKS_HOST`
5. Copy **HTTP path** → `DATABRICKS_HTTP_PATH`
6. Generate a PAT: **Settings → Developer → Access tokens → Generate new token**

### 4. Build and start

```bash
# First run — builds the image and runs one-time init
docker compose up --build -d

# Watch init logs (completes in ~2 minutes)
docker compose logs -f superset-init
```

When you see `✓ All done!`, open **http://localhost:8088**

Login with the credentials from your `.env` (`ADMIN_USERNAME` / `ADMIN_PASSWORD`).

### 5. Navigate to dashboards

| URL | Dashboard |
|---|---|
| http://localhost:8088/dashboard/makro-homepage/ | Homepage |
| http://localhost:8088/dashboard/makro-sales-performance/ | Sales Performance Insights |
| http://localhost:8088/dashboard/makro-data-exporter/ | Data Exporter |

---

## Row-Level Security (User-Level Permissions)

Superset's built-in RLS mirrors the `user_categories` logic from the original Streamlit app.

### Setup steps

1. Go to **Security → Row Level Security** in Superset
2. Click **+ Add Rule**
3. Configure per role/user:

| Field     | Value                        |
|-----------|------------------------------|
| Table     | `niq_sales_perf`             |
| Roles     | e.g. `Dry Food Buyer`        |
| Group key | `dry_food`                   |
| Clause    | `class_name IN ('DRY FOOD')` |

Repeat for each category. Users only see data matching their clause.

### Creating roles

1. **Security → List Roles → +**
2. Name: e.g. `Dry Food Buyer`
3. Assign permissions: `can read on Chart`, `can read on Dashboard`, `can read on Dataset`
4. Assign users to the role

---

## OAuth / SSO (optional)

To use Databricks OAuth U2M so each user authenticates with their own Databricks identity:

1. Uncomment the `AUTH_TYPE = AUTH_OAUTH` block in `superset_config.py`
2. Register an OAuth application in your Databricks account console
3. Add `DATABRICKS_CLIENT_ID` and `DATABRICKS_CLIENT_SECRET` to `.env`
4. Restart: `docker compose restart superset`

---

## Dashboard Filters

All three dashboards support Superset's native cross-filter, which replicates the sidebar filters from the Streamlit app:

- **Date range** — time range picker on all charts
- **Division / Class / Brand / Supplier / Product** — filter components linked to `niq_prod_hier`
- **Region / Store Format / Store Name** — filter components linked to `niq_sales_perf`

To add filters: open any dashboard → click **Filters** (top right) → **Edit dashboard** → **Add/edit filters**.

---

## Data Exporter

The **Data Exporter** dashboard includes:

- A full **Sales Data Export Table** chart with all columns
- Native Superset **CSV / Excel export** — click the `⋮` menu on the table chart → **Export to CSV** / **Export to Excel**
- **SQL Lab** — for ad-hoc queries: http://localhost:8088/sqllab/

---

## Re-running Bootstrap

If you need to re-create dashboards after clearing the DB:

```bash
docker compose run --rm superset-init
```

---

## Useful Commands

```bash
# View all service logs
docker compose logs -f

# Restart only the web server
docker compose restart superset

# Open a shell inside the Superset container
docker compose exec superset bash

# Stop everything
docker compose down

# Stop and remove all data (full reset)
docker compose down -v
```

---

## Production Checklist

- [ ] Set `SUPERSET_SECRET_KEY` to a strong random value
- [ ] Set `SESSION_COOKIE_SECURE = True` and `TALISMAN_CONFIG["force_https"] = True` in `superset_config.py`
- [ ] Put Superset behind a reverse proxy (nginx / Caddy) with HTTPS
- [ ] Replace PAT auth with OAuth U2M for per-user Databricks identity
- [ ] Configure RLS rules for all user roles
- [ ] Set up SMTP for Alerts & Reports
- [ ] Set up scheduled cache warming for heavy dashboards

---

## File Structure

```
makro-superset/
├── Dockerfile                  # Custom Superset image with Databricks driver
├── docker-compose.yml          # All services
├── superset_config.py          # Superset configuration (cache, RLS, OAuth, etc.)
├── requirements.txt            # Python packages (databricks-sql-connector, etc.)
├── .env.example                # Environment variable template
├── .gitignore
├── init/
│   ├── init_superset.sh        # Bootstrap: DB upgrade → admin user → init
│   └── bootstrap_dashboards.py # Creates DB connection, datasets, charts, dashboards
└── README.md
```

---

## Data Tables Used

| Table                   | Purpose                                                                                                                                                                                     |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `testdb.niq_sales_perf` | Sales fact: `sls_amt`, `sls_qty`, `no_trx`, `no_cust`, `day_sid`, `week_sid`, `store_no`, `store_name`, `region`, `store_format`, `class_name`, `brand`, `div_name`, `supplier`, `prod_num` |
| `testdb.niq_prod_hier`  | Product hierarchy: `prod_num`, `brand`, `supplier`, `class_name`, `div_name`                                                                                                                |
| `testdb.niq_user`       | User auth table (used by original Streamlit app, not needed in Superset)                                                                                                                    |
