"""
bootstrap_dashboards.py
========================
Programmatically creates:
  1. Databricks database connection
  2. Datasets (virtual tables / SQL views)
  3. Charts for each dashboard
  4. Three dashboards:
       A. Homepage          — Sales Growth Influencers (Brand / Geo / Store)
       B. Sales Performance — Trend & aggregated charts
       C. Data Exporter     — Ad-hoc SQL Lab + pre-built table chart

Runs once during `superset-init`. Safe to re-run (uses upsert logic).
"""

import os
import sys
import json
import time
import requests
from typing import Optional

# ─────────────────────────────────────────────
# Config from environment
# ─────────────────────────────────────────────

SUPERSET_URL = "http://localhost:8088"
ADMIN_USER = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASSWORD", "admin")

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "")
DATABRICKS_HTTP_PATH = os.environ.get("DATABRICKS_HTTP_PATH", "")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
DATABRICKS_CATALOG = os.environ.get("DATABRICKS_CATALOG", "hive_metastore")
DATABRICKS_SCHEMA = os.environ.get("DATABRICKS_SCHEMA", "testdb")


# ─────────────────────────────────────────────
# Superset API client
# ─────────────────────────────────────────────

class SupersetClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._login(username, password)

    def _login(self, username: str, password: str):
        """Obtain JWT access token"""
        resp = self.session.post(
            f"{self.base_url}/api/v1/security/login",
            json={"username": username, "password": password, "provider": "db", "refresh": True},
        )
        resp.raise_for_status()
        token = resp.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {token}"})

        # Fetch CSRF token
        csrf_resp = self.session.get(f"{self.base_url}/api/v1/security/csrf_token/")
        csrf_resp.raise_for_status()
        csrf_token = csrf_resp.json()["result"]
        self.session.headers.update({"X-CSRFToken": csrf_token, "Referer": self.base_url})

    def get(self, path: str, **kwargs):
        r = self.session.get(f"{self.base_url}{path}", **kwargs)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, **kwargs):
        r = self.session.post(f"{self.base_url}{path}", **kwargs)
        r.raise_for_status()
        return r.json()

    def put(self, path: str, **kwargs):
        r = self.session.put(f"{self.base_url}{path}", **kwargs)
        r.raise_for_status()
        return r.json()

    def find_or_create(self, list_path: str, create_path: str, filter_key: str,
                       filter_val: str, payload: dict) -> int:
        """Upsert: find existing by filter_key==filter_val, else create."""
        result = self.get(f"{list_path}?q=(filters:!((col:{filter_key},opr:eq,val:'{filter_val}')))")
        items = result.get("result", [])
        if items:
            print(f"    ✓ Already exists: {filter_val}")
            return items[0]["id"]
        resp = self.post(create_path, json=payload)
        new_id = resp.get("id") or resp.get("result", {}).get("id")
        print(f"    + Created: {filter_val} (id={new_id})")
        return new_id


# ─────────────────────────────────────────────
# Wait for Superset to be healthy
# ─────────────────────────────────────────────

def wait_for_superset(url: str, retries: int = 20, delay: int = 5):
    print(f"Waiting for Superset at {url}/health ...")
    for i in range(retries):
        try:
            r = requests.get(f"{url}/health", timeout=5)
            if r.ok:
                print("  Superset is up ✓")
                return
        except Exception:
            pass
        print(f"  Not ready yet, retry {i+1}/{retries} ...")
        time.sleep(delay)
    print("ERROR: Superset did not start in time. Exiting.")
    sys.exit(1)


# ─────────────────────────────────────────────
# 1. Create Databricks database connection
# ─────────────────────────────────────────────

def create_database(client: SupersetClient) -> int:
    """Register the Databricks SQL Warehouse as a Superset database."""
    print("\n[Step 1] Registering Databricks connection...")

    # SQLAlchemy URI for Databricks
    # Format: databricks+connector://token:{token}@{host}:443/{schema}?http_path={http_path}&catalog={catalog}
    sqlalchemy_uri = (
        f"databricks+connector://token:{DATABRICKS_TOKEN}"
        f"@{DATABRICKS_HOST}:443/{DATABRICKS_SCHEMA}"
        f"?http_path={DATABRICKS_HTTP_PATH}"
        f"&catalog={DATABRICKS_CATALOG}"
    )

    payload = {
        "database_name": "Makro Databricks",
        "sqlalchemy_uri": sqlalchemy_uri,
        "expose_in_sqllab": True,
        "allow_run_async": True,
        "allow_ctas": False,
        "allow_cvas": False,
        "allow_dml": False,
        "allow_multi_schema_metadata_fetch": True,
        "allow_csv_upload": False,
        "extra": json.dumps({
            "engine_params": {},
            "metadata_params": {},
            "schemas_allowed_for_file_upload": [],
            "cost_estimate_enabled": False,
        }),
    }

    db_id = client.find_or_create(
        list_path="/api/v1/database",
        create_path="/api/v1/database",
        filter_key="database_name",
        filter_val="Makro Databricks",
        payload=payload,
    )
    return db_id


# ─────────────────────────────────────────────
# 2. Create datasets (virtual tables / SQL)
# ─────────────────────────────────────────────

DATASETS = {
    # ── niq_sales_perf — main sales fact table ──────────────────────────────
    "niq_sales_perf": {
        "table_name": "niq_sales_perf",
        "schema": DATABRICKS_SCHEMA,
        "is_managed_externally": False,
        "description": "Main sales performance fact table. Granularity: store × product × day.",
    },
    # ── niq_prod_hier — product hierarchy ──────────────────────────────────
    "niq_prod_hier": {
        "table_name": "niq_prod_hier",
        "schema": DATABRICKS_SCHEMA,
        "is_managed_externally": False,
        "description": "Product hierarchy: Division → Class → Brand → Supplier → Product.",
    },
    # ── vw_homepage_winners_losers — virtual dataset for Homepage ──────────
    "vw_homepage_brand_growth": {
        "table_name": "vw_homepage_brand_growth",
        "schema": DATABRICKS_SCHEMA,
        "sql": """
            -- Virtual dataset: Brand YoY growth (last 30 days vs same period LY)
            WITH cy AS (
                SELECT brand,
                       SUM(sls_amt) AS cy_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 30), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(CURRENT_DATE, 'yyyyMMdd') AS INT)
                GROUP BY brand
            ),
            ly AS (
                SELECT brand,
                       SUM(sls_amt) AS ly_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 395), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 365), 'yyyyMMdd') AS INT)
                GROUP BY brand
            )
            SELECT COALESCE(cy.brand, ly.brand)        AS brand,
                   COALESCE(cy.cy_sales, 0)             AS cy_sales,
                   COALESCE(ly.ly_sales, 0)             AS ly_sales,
                   COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0) AS growth_abs,
                   CASE WHEN COALESCE(ly.ly_sales, 0) > 0
                        THEN (COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0)) / ly.ly_sales * 100
                        ELSE NULL END                   AS growth_pct
            FROM cy
            FULL OUTER JOIN ly ON cy.brand = ly.brand
        """,
        "description": "Brand YoY sales growth — last 30 days vs same period last year.",
    },
    "vw_homepage_geo_growth": {
        "table_name": "vw_homepage_geo_growth",
        "schema": DATABRICKS_SCHEMA,
        "sql": """
            WITH cy AS (
                SELECT region,
                       SUM(sls_amt) AS cy_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 30), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(CURRENT_DATE, 'yyyyMMdd') AS INT)
                GROUP BY region
            ),
            ly AS (
                SELECT region,
                       SUM(sls_amt) AS ly_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 395), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 365), 'yyyyMMdd') AS INT)
                GROUP BY region
            )
            SELECT COALESCE(cy.region, ly.region)       AS region,
                   COALESCE(cy.cy_sales, 0)              AS cy_sales,
                   COALESCE(ly.ly_sales, 0)              AS ly_sales,
                   COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0) AS growth_abs,
                   CASE WHEN COALESCE(ly.ly_sales, 0) > 0
                        THEN (COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0)) / ly.ly_sales * 100
                        ELSE NULL END                    AS growth_pct
            FROM cy
            FULL OUTER JOIN ly ON cy.region = ly.region
        """,
        "description": "Region YoY sales growth.",
    },
    "vw_homepage_store_growth": {
        "table_name": "vw_homepage_store_growth",
        "schema": DATABRICKS_SCHEMA,
        "sql": """
            WITH cy AS (
                SELECT store_name,
                       SUM(sls_amt) AS cy_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 30), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(CURRENT_DATE, 'yyyyMMdd') AS INT)
                GROUP BY store_name
            ),
            ly AS (
                SELECT store_name,
                       SUM(sls_amt) AS ly_sales
                FROM   testdb.niq_sales_perf
                WHERE  day_sid BETWEEN
                           CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 395), 'yyyyMMdd') AS INT)
                           AND CAST(DATE_FORMAT(DATE_SUB(CURRENT_DATE, 365), 'yyyyMMdd') AS INT)
                GROUP BY store_name
            )
            SELECT COALESCE(cy.store_name, ly.store_name) AS store_name,
                   COALESCE(cy.cy_sales, 0)                AS cy_sales,
                   COALESCE(ly.ly_sales, 0)                AS ly_sales,
                   COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0) AS growth_abs,
                   CASE WHEN COALESCE(ly.ly_sales, 0) > 0
                        THEN (COALESCE(cy.cy_sales, 0) - COALESCE(ly.ly_sales, 0)) / ly.ly_sales * 100
                        ELSE NULL END                      AS growth_pct
            FROM cy
            FULL OUTER JOIN ly ON cy.store_name = ly.store_name
        """,
        "description": "Store YoY sales growth.",
    },
    "vw_daily_sales_trend": {
        "table_name": "vw_daily_sales_trend",
        "schema": DATABRICKS_SCHEMA,
        "sql": """
            SELECT
                TO_DATE(CAST(day_sid AS STRING), 'yyyyMMdd')  AS sale_date,
                week_sid,
                class_name,
                div_name,
                brand,
                supplier,
                region,
                store_format,
                store_name,
                SUM(sls_amt)                                  AS total_sales,
                SUM(sls_qty)                                  AS total_quantity,
                SUM(no_trx)                                   AS total_transactions,
                SUM(no_cust)                                  AS total_customers,
                COUNT(DISTINCT store_no)                      AS unique_stores
            FROM testdb.niq_sales_perf
            GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
        """,
        "description": "Daily sales trend — pre-aggregated for Sales Performance Insights charts.",
    },
}


def create_datasets(client: SupersetClient, db_id: int) -> dict:
    """Create all virtual datasets. Returns {name: id} mapping."""
    print("\n[Step 2] Creating datasets...")
    dataset_ids = {}

    for ds_key, ds_config in DATASETS.items():
        payload = {
            "database": db_id,
            "table_name": ds_config["table_name"],
            "schema": ds_config.get("schema", DATABRICKS_SCHEMA),
            "description": ds_config.get("description", ""),
        }
        if "sql" in ds_config:
            payload["sql"] = ds_config["sql"]

        ds_id = client.find_or_create(
            list_path="/api/v1/dataset",
            create_path="/api/v1/dataset",
            filter_key="table_name",
            filter_val=ds_config["table_name"],
            payload=payload,
        )
        dataset_ids[ds_key] = ds_id

    return dataset_ids


# ─────────────────────────────────────────────
# 3. Create charts
# ─────────────────────────────────────────────

def create_charts(client: SupersetClient, dataset_ids: dict) -> dict:
    """Create all charts. Returns {name: id} mapping."""
    print("\n[Step 3] Creating charts...")
    chart_ids = {}

    charts = [
        # ── Homepage: Sales Growth Influencers ─────────────────────────────

        {
            "slice_name": "Brand Sales Growth (Winner/Loser)",
            "viz_type": "bar",
            "datasource_id": dataset_ids["vw_homepage_brand_growth"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "bar",
                "metrics": ["growth_abs"],
                "groupby": ["brand"],
                "row_limit": 20,
                "order_desc": True,
                "color_scheme": "bnbColors",
                "y_axis_format": ",.0f",
                "x_axis_label": "Brand",
                "y_axis_label": "Sales Growth (THB)",
                "rich_tooltip": True,
                "bar_stacked": False,
                "show_legend": False,
                "contribution": False,
            }),
        },
        {
            "slice_name": "Geo Sales Growth (Winner/Loser)",
            "viz_type": "bar",
            "datasource_id": dataset_ids["vw_homepage_geo_growth"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "bar",
                "metrics": ["growth_abs"],
                "groupby": ["region"],
                "row_limit": 20,
                "order_desc": True,
                "color_scheme": "bnbColors",
                "y_axis_format": ",.0f",
                "x_axis_label": "Region",
                "y_axis_label": "Sales Growth (THB)",
                "rich_tooltip": True,
                "bar_stacked": False,
                "show_legend": False,
            }),
        },
        {
            "slice_name": "Store Sales Growth (Winner/Loser)",
            "viz_type": "bar",
            "datasource_id": dataset_ids["vw_homepage_store_growth"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "bar",
                "metrics": ["growth_abs"],
                "groupby": ["store_name"],
                "row_limit": 20,
                "order_desc": True,
                "color_scheme": "bnbColors",
                "y_axis_format": ",.0f",
                "x_axis_label": "Store",
                "y_axis_label": "Sales Growth (THB)",
                "rich_tooltip": True,
                "bar_stacked": False,
                "show_legend": False,
            }),
        },
        # Homepage scorecards
        {
            "slice_name": "Total Sales (THB)",
            "viz_type": "big_number_total",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "big_number_total",
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_sales"}, "aggregate": "SUM", "label": "Sales (THB)"},
                "subheader": "Total Sales",
                "y_axis_format": ",.0f",
                "header_font_size": 0.3,
                "time_range": "Last month",
            }),
        },
        {
            "slice_name": "Total Units Sold",
            "viz_type": "big_number_total",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "big_number_total",
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_quantity"}, "aggregate": "SUM", "label": "Units Sold"},
                "subheader": "Units Sold",
                "y_axis_format": ",.0f",
                "time_range": "Last month",
            }),
        },
        {
            "slice_name": "Total Shoppers",
            "viz_type": "big_number_total",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "big_number_total",
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_customers"}, "aggregate": "SUM", "label": "Shoppers"},
                "subheader": "Shoppers",
                "y_axis_format": ",.0f",
                "time_range": "Last month",
            }),
        },
        {
            "slice_name": "Total Trips",
            "viz_type": "big_number_total",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "big_number_total",
                "metric": {"expressionType": "SIMPLE", "column": {"column_name": "total_transactions"}, "aggregate": "SUM", "label": "Trips"},
                "subheader": "Trips",
                "y_axis_format": ",.0f",
                "time_range": "Last month",
            }),
        },

        # ── Sales Performance Insights ──────────────────────────────────────

        {
            "slice_name": "Sales Trend (Daily/Weekly)",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_sales"}, "aggregate": "SUM", "label": "Sales (THB)"}],
                "time_grain_sqla": "P1D",
                "row_limit": 50000,
                "y_axis_format": ",.0f",
                "rich_tooltip": True,
                "show_legend": True,
                "zoomable": True,
                "area": False,
                "color_scheme": "supersetColors",
            }),
        },
        {
            "slice_name": "Unit Sales Trend",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_quantity"}, "aggregate": "SUM", "label": "Units"}],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.0f",
                "color_scheme": "emeraldColors",
                "zoomable": True,
            }),
        },
        {
            "slice_name": "Trips Trend",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "total_transactions"}, "aggregate": "SUM", "label": "Trips"}],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.0f",
                "color_scheme": "airbnbColors",
                "zoomable": True,
            }),
        },
        {
            "slice_name": "THB per Trip",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{
                    "expressionType": "SQL",
                    "sqlExpression": "SUM(total_sales) / NULLIF(SUM(total_transactions), 0)",
                    "label": "THB / Trip",
                }],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.2f",
                "zoomable": True,
            }),
        },
        {
            "slice_name": "Units per Trip",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{
                    "expressionType": "SQL",
                    "sqlExpression": "SUM(total_quantity) / NULLIF(SUM(total_transactions), 0)",
                    "label": "Units / Trip",
                }],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.2f",
                "zoomable": True,
            }),
        },
        {
            "slice_name": "Avg Price per Unit",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{
                    "expressionType": "SQL",
                    "sqlExpression": "SUM(total_sales) / NULLIF(SUM(total_quantity), 0)",
                    "label": "Avg Price / Unit",
                }],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.2f",
                "zoomable": True,
            }),
        },
        {
            "slice_name": "# Selling Stores",
            "viz_type": "echarts_timeseries_line",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "echarts_timeseries_line",
                "x_axis": "sale_date",
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "unique_stores"}, "aggregate": "SUM", "label": "Stores"}],
                "time_grain_sqla": "P1D",
                "y_axis_format": ",.0f",
                "zoomable": True,
            }),
        },
        # Aggregated table for Sales Performance → Table View
        {
            "slice_name": "Top 10 Products by Sales",
            "viz_type": "table",
            "datasource_id": dataset_ids["niq_sales_perf"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "table",
                "query_mode": "aggregate",
                "groupby": ["prod_num"],
                "metrics": [
                    {"expressionType": "SIMPLE", "column": {"column_name": "sls_amt"}, "aggregate": "SUM", "label": "Sales (THB)"},
                    {"expressionType": "SIMPLE", "column": {"column_name": "sls_qty"}, "aggregate": "SUM", "label": "Units"},
                ],
                "row_limit": 10,
                "order_desc": True,
                "include_search": True,
                "table_timestamp_format": "%Y-%m-%d",
            }),
        },

        # ── Data Exporter ──────────────────────────────────────────────────
        {
            "slice_name": "Sales Data Export Table",
            "viz_type": "table",
            "datasource_id": dataset_ids["vw_daily_sales_trend"],
            "datasource_type": "table",
            "params": json.dumps({
                "viz_type": "table",
                "query_mode": "raw",
                "all_columns": [
                    "sale_date", "class_name", "div_name", "brand", "supplier",
                    "region", "store_format", "store_name",
                    "total_sales", "total_quantity", "total_transactions", "total_customers", "unique_stores",
                ],
                "row_limit": 10000,
                "order_desc": True,
                "include_search": True,
                "page_length": 50,
                "show_cell_bars": True,
                "align_pn": False,
                "color_pn": True,
                "allow_rearrange_columns": True,
            }),
        },
    ]

    for chart_def in charts:
        chart_id = client.find_or_create(
            list_path="/api/v1/chart",
            create_path="/api/v1/chart",
            filter_key="slice_name",
            filter_val=chart_def["slice_name"],
            payload=chart_def,
        )
        chart_ids[chart_def["slice_name"]] = chart_id

    return chart_ids


# ─────────────────────────────────────────────
# 4. Create dashboards
# ─────────────────────────────────────────────

def create_dashboards(client: SupersetClient, chart_ids: dict):
    """Create the three Makro dashboards."""
    print("\n[Step 4] Creating dashboards...")

    dashboards = [
        {
            "dashboard_title": "Homepage — Sales Growth Influencers",
            "slug": "makro-homepage",
            "published": True,
            "position_json": json.dumps({
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [
                    "ROW-scores", "ROW-charts"
                ], "parents": ["ROOT_ID"]},
                "ROW-scores": {
                    "type": "ROW", "id": "ROW-scores",
                    "children": ["COL-s1", "COL-s2", "COL-s3", "COL-s4"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-s1": {"type": "COLUMN", "id": "COL-s1", "children": ["CHART-total-sales"],
                           "parents": ["ROOT_ID", "GRID_ID", "ROW-scores"], "meta": {"width": 3, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-total-sales": {"type": "CHART", "id": "CHART-total-sales",
                                      "meta": {"chartId": chart_ids.get("Total Sales (THB)", 0), "width": 3, "height": 10},
                                      "parents": ["ROOT_ID", "GRID_ID", "ROW-scores", "COL-s1"]},
                "COL-s2": {"type": "COLUMN", "id": "COL-s2", "children": ["CHART-units"],
                           "parents": ["ROOT_ID", "GRID_ID", "ROW-scores"], "meta": {"width": 3, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-units": {"type": "CHART", "id": "CHART-units",
                                "meta": {"chartId": chart_ids.get("Total Units Sold", 0), "width": 3, "height": 10},
                                "parents": ["ROOT_ID", "GRID_ID", "ROW-scores", "COL-s2"]},
                "COL-s3": {"type": "COLUMN", "id": "COL-s3", "children": ["CHART-shoppers"],
                           "parents": ["ROOT_ID", "GRID_ID", "ROW-scores"], "meta": {"width": 3, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-shoppers": {"type": "CHART", "id": "CHART-shoppers",
                                   "meta": {"chartId": chart_ids.get("Total Shoppers", 0), "width": 3, "height": 10},
                                   "parents": ["ROOT_ID", "GRID_ID", "ROW-scores", "COL-s3"]},
                "COL-s4": {"type": "COLUMN", "id": "COL-s4", "children": ["CHART-trips"],
                           "parents": ["ROOT_ID", "GRID_ID", "ROW-scores"], "meta": {"width": 3, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-trips": {"type": "CHART", "id": "CHART-trips",
                                "meta": {"chartId": chart_ids.get("Total Trips", 0), "width": 3, "height": 10},
                                "parents": ["ROOT_ID", "GRID_ID", "ROW-scores", "COL-s4"]},
                "ROW-charts": {
                    "type": "ROW", "id": "ROW-charts",
                    "children": ["COL-brand", "COL-geo", "COL-store"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-brand": {"type": "COLUMN", "id": "COL-brand", "children": ["CHART-brand"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-charts"], "meta": {"width": 4, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-brand": {"type": "CHART", "id": "CHART-brand",
                                "meta": {"chartId": chart_ids.get("Brand Sales Growth (Winner/Loser)", 0), "width": 4, "height": 50},
                                "parents": ["ROOT_ID", "GRID_ID", "ROW-charts", "COL-brand"]},
                "COL-geo": {"type": "COLUMN", "id": "COL-geo", "children": ["CHART-geo"],
                            "parents": ["ROOT_ID", "GRID_ID", "ROW-charts"], "meta": {"width": 4, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-geo": {"type": "CHART", "id": "CHART-geo",
                              "meta": {"chartId": chart_ids.get("Geo Sales Growth (Winner/Loser)", 0), "width": 4, "height": 50},
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-charts", "COL-geo"]},
                "COL-store": {"type": "COLUMN", "id": "COL-store", "children": ["CHART-store"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-charts"], "meta": {"width": 4, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-store": {"type": "CHART", "id": "CHART-store",
                                "meta": {"chartId": chart_ids.get("Store Sales Growth (Winner/Loser)", 0), "width": 4, "height": 50},
                                "parents": ["ROOT_ID", "GRID_ID", "ROW-charts", "COL-store"]},
            }),
        },
        {
            "dashboard_title": "Sales Performance Insights",
            "slug": "makro-sales-performance",
            "published": True,
            "position_json": json.dumps({
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [
                    "ROW-main", "ROW-row1", "ROW-row2", "ROW-row3"
                ], "parents": ["ROOT_ID"]},
                "ROW-main": {
                    "type": "ROW", "id": "ROW-main",
                    "children": ["COL-main"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-main": {"type": "COLUMN", "id": "COL-main", "children": ["CHART-sales-trend"],
                             "parents": ["ROOT_ID", "GRID_ID", "ROW-main"],
                             "meta": {"width": 12, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-sales-trend": {"type": "CHART", "id": "CHART-sales-trend",
                                      "meta": {"chartId": chart_ids.get("Sales Trend (Daily/Weekly)", 0), "width": 12, "height": 50},
                                      "parents": ["ROOT_ID", "GRID_ID", "ROW-main", "COL-main"]},
                "ROW-row1": {
                    "type": "ROW", "id": "ROW-row1",
                    "children": ["COL-units", "COL-trips"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-units": {"type": "COLUMN", "id": "COL-units", "children": ["CHART-units-trend"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-row1"],
                              "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-units-trend": {"type": "CHART", "id": "CHART-units-trend",
                                      "meta": {"chartId": chart_ids.get("Unit Sales Trend", 0), "width": 6, "height": 35},
                                      "parents": ["ROOT_ID", "GRID_ID", "ROW-row1", "COL-units"]},
                "COL-trips": {"type": "COLUMN", "id": "COL-trips", "children": ["CHART-trips-trend"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-row1"],
                              "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-trips-trend": {"type": "CHART", "id": "CHART-trips-trend",
                                      "meta": {"chartId": chart_ids.get("Trips Trend", 0), "width": 6, "height": 35},
                                      "parents": ["ROOT_ID", "GRID_ID", "ROW-row1", "COL-trips"]},
                "ROW-row2": {
                    "type": "ROW", "id": "ROW-row2",
                    "children": ["COL-thb", "COL-upt"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-thb": {"type": "COLUMN", "id": "COL-thb", "children": ["CHART-thb"],
                            "parents": ["ROOT_ID", "GRID_ID", "ROW-row2"],
                            "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-thb": {"type": "CHART", "id": "CHART-thb",
                              "meta": {"chartId": chart_ids.get("THB per Trip", 0), "width": 6, "height": 35},
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-row2", "COL-thb"]},
                "COL-upt": {"type": "COLUMN", "id": "COL-upt", "children": ["CHART-upt"],
                            "parents": ["ROOT_ID", "GRID_ID", "ROW-row2"],
                            "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-upt": {"type": "CHART", "id": "CHART-upt",
                              "meta": {"chartId": chart_ids.get("Units per Trip", 0), "width": 6, "height": 35},
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-row2", "COL-upt"]},
                "ROW-row3": {
                    "type": "ROW", "id": "ROW-row3",
                    "children": ["COL-price", "COL-stores"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-price": {"type": "COLUMN", "id": "COL-price", "children": ["CHART-price"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-row3"],
                              "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-price": {"type": "CHART", "id": "CHART-price",
                                "meta": {"chartId": chart_ids.get("Avg Price per Unit", 0), "width": 6, "height": 35},
                                "parents": ["ROOT_ID", "GRID_ID", "ROW-row3", "COL-price"]},
                "COL-stores": {"type": "COLUMN", "id": "COL-stores", "children": ["CHART-stores"],
                               "parents": ["ROOT_ID", "GRID_ID", "ROW-row3"],
                               "meta": {"width": 6, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-stores": {"type": "CHART", "id": "CHART-stores",
                                 "meta": {"chartId": chart_ids.get("# Selling Stores", 0), "width": 6, "height": 35},
                                 "parents": ["ROOT_ID", "GRID_ID", "ROW-row3", "COL-stores"]},
            }),
        },
        {
            "dashboard_title": "Data Exporter",
            "slug": "makro-data-exporter",
            "published": True,
            "position_json": json.dumps({
                "DASHBOARD_VERSION_KEY": "v2",
                "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
                "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": ["ROW-export"],
                            "parents": ["ROOT_ID"]},
                "ROW-export": {
                    "type": "ROW", "id": "ROW-export",
                    "children": ["COL-table"],
                    "parents": ["ROOT_ID", "GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                },
                "COL-table": {"type": "COLUMN", "id": "COL-table", "children": ["CHART-export-table"],
                              "parents": ["ROOT_ID", "GRID_ID", "ROW-export"],
                              "meta": {"width": 12, "background": "BACKGROUND_TRANSPARENT"}},
                "CHART-export-table": {
                    "type": "CHART", "id": "CHART-export-table",
                    "meta": {"chartId": chart_ids.get("Sales Data Export Table", 0), "width": 12, "height": 120},
                    "parents": ["ROOT_ID", "GRID_ID", "ROW-export", "COL-table"]},
            }),
        },
    ]

    for dash in dashboards:
        d_id = client.find_or_create(
            list_path="/api/v1/dashboard",
            create_path="/api/v1/dashboard",
            filter_key="slug",
            filter_val=dash["slug"],
            payload=dash,
        )
        print(f"  Dashboard ready: {dash['dashboard_title']} (id={d_id})")


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
        print("WARNING: DATABRICKS_HOST or DATABRICKS_TOKEN not set — skipping Databricks setup.")
        print("  Set them in .env and re-run `docker compose run --rm superset-init`")
        sys.exit(0)

    wait_for_superset(SUPERSET_URL)

    print(f"\nConnecting to Superset as '{ADMIN_USER}'...")
    client = SupersetClient(SUPERSET_URL, ADMIN_USER, ADMIN_PASS)

    db_id = create_database(client)
    dataset_ids = create_datasets(client, db_id)
    chart_ids = create_charts(client, dataset_ids)
    create_dashboards(client, chart_ids)

    print("\n✓ All done! Open http://localhost:8088 to view your dashboards.")
