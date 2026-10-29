"""
In-House BI Data Product - FastAPI Backend
==========================================
Exposes aggregated e-commerce metrics as REST API.
Serves the React dashboard frontend.

Endpoints:
  GET /api/v1/kpi/summary          - Overall KPIs
  GET /api/v1/gmv/daily            - Daily GMV trend
  GET /api/v1/gmv/realtime         - Live GMV (last 24h from ClickHouse)
  GET /api/v1/products/top         - Top performing products
  GET /api/v1/sellers/scorecard    - Seller performance
  GET /api/v1/customers/rfm        - RFM segments
  GET /api/v1/categories/trends    - Category trends
  GET /api/v1/warehouse/status     - Warehouse inventory status
  GET /api/v1/funnel                - Conversion funnel
  WS  /ws/live-orders              - WebSocket real-time order stream
"""
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import logging
import random
from datetime import datetime, timedelta, date
from typing import Optional

import clickhouse_driver
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bi-api")

app = FastAPI(
    title="EComm BI Data Product API",
    description="Real-time & batch analytics API for e-commerce platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DB Clients ────────────────────────────────────────────────
# ClickHouse (real-time)
def get_ch_client():
    return clickhouse_driver.Client(
        host="localhost", port=9000, database="ecomm_realtime"
    )

# Databricks SQL (batch ADS layer) - mock for demo
# In production: use databricks-sql-connector
def query_ads(sql: str) -> pd.DataFrame:
    """Mock ADS query - replace with actual Databricks SQL connector."""
    # from databricks import sql
    # conn = sql.connect(server_hostname=..., http_path=..., access_token=...)
    return pd.DataFrame()  # placeholder


# ── Dummy data generator for demo ─────────────────────────────
def mock_daily_gmv(days: int = 30) -> list:
    base = datetime.now().date()
    data = []
    gmv = 500000
    for i in range(days, 0, -1):
        d = base - timedelta(days=i)
        gmv = gmv * random.uniform(0.95, 1.08)
        data.append({
            "date": str(d),
            "gmv": round(gmv, 2),
            "orders": random.randint(800, 2000),
            "unique_buyers": random.randint(600, 1500),
            "aov": round(gmv / random.randint(800, 2000), 2),
        })
    return data


def mock_kpi() -> dict:
    return {
        "gmv_today": round(random.uniform(400000, 800000), 2),
        "gmv_yesterday": round(random.uniform(380000, 750000), 2),
        "gmv_mtd": round(random.uniform(8000000, 15000000), 2),
        "orders_today": random.randint(800, 2000),
        "orders_yesterday": random.randint(750, 1900),
        "active_sellers": random.randint(40, 55),
        "unique_buyers_today": random.randint(600, 1500),
        "avg_order_value": round(random.uniform(400, 800), 2),
        "completion_rate_pct": round(random.uniform(85, 95), 1),
        "cancellation_rate_pct": round(random.uniform(3, 8), 1),
        "platform_revenue_today": round(random.uniform(20000, 50000), 2),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ── Routes ────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}


@app.get("/api/v1/kpi/summary")
async def get_kpi_summary():
    """Overall KPI summary - Today vs Yesterday comparison."""
    return {"data": mock_kpi(), "source": "ecomm_ads.ads_daily_gmv"}


@app.get("/api/v1/gmv/daily")
async def get_daily_gmv(
    days: int = Query(default=30, ge=1, le=365, description="Lookback days"),
    granularity: str = Query(default="daily", enum=["daily", "weekly", "monthly"]),
):
    """Daily GMV trend with WoW / MoM comparison."""
    data = mock_daily_gmv(days)

    # WoW change
    for i, row in enumerate(data):
        prev_week_idx = i - 7
        if prev_week_idx >= 0:
            row["wow_change_pct"] = round(
                (row["gmv"] - data[prev_week_idx]["gmv"]) / data[prev_week_idx]["gmv"] * 100, 1
            )
        else:
            row["wow_change_pct"] = None

    return {"data": data, "granularity": granularity, "source": "ecomm_ads.ads_daily_gmv"}


@app.get("/api/v1/gmv/realtime")
async def get_realtime_gmv(hours: int = Query(default=24, ge=1, le=168)):
    """Real-time GMV from ClickHouse (last N hours)."""
    try:
        client = get_ch_client()
        result = client.execute("""
            SELECT
                toStartOfHour(event_time) AS hour,
                city,
                count()                   AS orders,
                sum(total_amount)         AS gmv,
                uniqExact(user_id)        AS buyers
            FROM rt_orders_stream
            WHERE event_time >= now() - INTERVAL %(hours)s HOUR
              AND op = 'c'
            GROUP BY hour, city
            ORDER BY hour DESC, gmv DESC
        """, {"hours": hours})

        data = [
            {"hour": str(row[0]), "city": row[1], "orders": row[2],
             "gmv": float(row[3]), "buyers": row[4]}
            for row in result
        ]
        return {"data": data, "source": "clickhouse.rt_orders_stream"}
    except Exception as e:
        logger.warning(f"ClickHouse unavailable, returning mock: {e}")
        # Fallback mock
        data = []
        for h in range(hours, 0, -1):
            ts = datetime.utcnow() - timedelta(hours=h)
            data.append({
                "hour": ts.strftime("%Y-%m-%dT%H:00:00"),
                "city": random.choice(["Bangkok", "Chiang Mai", "Phuket"]),
                "orders": random.randint(10, 100),
                "gmv": round(random.uniform(5000, 80000), 2),
                "buyers": random.randint(8, 80),
            })
        return {"data": data, "source": "mock"}


@app.get("/api/v1/products/top")
async def get_top_products(
    limit: int = Query(default=10, ge=1, le=100),
    category: Optional[str] = None,
    sort_by: str = Query(default="revenue", enum=["revenue", "units", "rating"]),
    period_days: int = Query(default=30, ge=7, le=365),
):
    """Top performing products by revenue / units / rating."""
    products = []
    categories = ["Smartphones", "Laptops", "Audio", "Fashion", "Kitchen", "Beauty"]
    for i in range(limit):
        cat = category or random.choice(categories)
        products.append({
            "rank": i + 1,
            "product_id": random.randint(1, 200),
            "product_name": f"Product {random.randint(100, 999)} - {cat}",
            "category": cat,
            "brand": random.choice(["Samsung", "Apple", "Nike", "Sony", "L'Oreal"]),
            "total_revenue": round(random.uniform(50000, 500000), 2),
            "units_sold": random.randint(100, 5000),
            "avg_selling_price": round(random.uniform(200, 5000), 2),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(10, 2000),
            "return_rate_pct": round(random.uniform(0.5, 5.0), 1),
            "revenue_wow_change_pct": round(random.uniform(-10, 20), 1),
        })
    sort_key = {"revenue": "total_revenue", "units": "units_sold", "rating": "rating"}[sort_by]
    products = sorted(products, key=lambda x: x[sort_key], reverse=True)
    return {"data": products, "period_days": period_days, "source": "ecomm_ads.ads_product_performance"}


@app.get("/api/v1/sellers/scorecard")
async def get_seller_scorecard(
    tier: Optional[str] = Query(default=None, enum=["Platinum", "Gold", "Silver", "Standard"]),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Seller performance scorecard."""
    sellers = []
    tiers = ["Platinum", "Gold", "Silver", "Standard"]
    for i in range(limit):
        t = tier or random.choice(tiers)
        sellers.append({
            "rank": i + 1,
            "seller_id": random.randint(1, 50),
            "shop_name": f"Shop {random.randint(100, 999)}",
            "tier": t,
            "total_gmv": round(random.uniform(100000, 5000000), 2),
            "total_orders": random.randint(500, 20000),
            "unique_customers": random.randint(200, 10000),
            "avg_order_value": round(random.uniform(300, 1500), 2),
            "fulfillment_rate_pct": round(random.uniform(85, 99), 1),
            "avg_fulfillment_days": round(random.uniform(1.5, 5.0), 1),
            "cancellation_rate_pct": round(random.uniform(1, 8), 1),
            "seller_rating": round(random.uniform(3.5, 5.0), 2),
            "commission_paid": round(random.uniform(5000, 250000), 2),
            "gmv_last_30d": round(random.uniform(20000, 400000), 2),
        })
    return {"data": sellers, "source": "ecomm_ads.ads_seller_scorecard"}


@app.get("/api/v1/customers/rfm")
async def get_customer_rfm():
    """Customer RFM segment distribution."""
    segments = ["Champions", "Loyal Customers", "New Customers", "Potential Loyalists",
                "At Risk", "Needs Attention", "Lost Customers"]
    weights = [15, 20, 18, 17, 12, 10, 8]
    total = 500

    data = []
    for seg, w in zip(segments, weights):
        count = int(total * w / 100)
        data.append({
            "segment": seg,
            "customer_count": count,
            "percentage": w,
            "avg_monetary": round(random.uniform(500, 50000), 2),
            "avg_frequency": round(random.uniform(1, 20), 1),
            "avg_recency_days": random.randint(1, 180),
            "total_revenue": round(count * random.uniform(500, 5000), 2),
        })
    return {"data": data, "total_customers": total, "source": "ecomm_ads.ads_customer_rfm"}


@app.get("/api/v1/categories/trends")
async def get_category_trends(days: int = Query(default=30, ge=7, le=90)):
    """Category revenue trends."""
    categories = ["Smartphones", "Laptops", "Fashion", "Beauty", "Kitchen", "Sports"]
    data = []
    for cat in categories:
        base_rev = random.uniform(100000, 1000000)
        trend_data = []
        for i in range(days):
            d = datetime.now().date() - timedelta(days=days - i)
            trend_data.append({
                "date": str(d),
                "revenue": round(base_rev * random.uniform(0.8, 1.2) / days, 2),
            })
        data.append({
            "category": cat,
            "total_revenue_period": round(base_rev, 2),
            "growth_rate_pct": round(random.uniform(-5, 25), 1),
            "trend": trend_data,
        })
    return {"data": data, "period_days": days, "source": "ecomm_ads.ads_category_trends"}


@app.get("/api/v1/warehouse/status")
async def get_warehouse_status():
    """Warehouse inventory status and efficiency metrics."""
    warehouses = ["BKK-01", "BKK-02", "CNX-01", "HKT-01", "KKN-01"]
    data = []
    for code in warehouses:
        utilization = random.uniform(45, 95)
        data.append({
            "warehouse_code": code,
            "city": code.split("-")[0].replace("BKK", "Bangkok")
                    .replace("CNX", "Chiang Mai").replace("HKT", "Phuket").replace("KKN", "Khon Kaen"),
            "total_skus": random.randint(500, 3000),
            "available_units": random.randint(5000, 50000),
            "capacity_utilization_pct": round(utilization, 1),
            "stockout_skus": random.randint(0, 50),
            "stockout_rate_pct": round(random.uniform(0, 5), 1),
            "skus_needing_reorder": random.randint(5, 100),
            "inventory_value": round(random.uniform(500000, 5000000), 2),
            "avg_delivery_days": round(random.uniform(1.5, 4.0), 1),
            "fulfillment_rate_pct": round(random.uniform(88, 99), 1),
            "status": "warning" if utilization > 90 else ("ok" if utilization > 50 else "low"),
        })
    return {"data": data, "source": "ecomm_ads.ads_warehouse_efficiency"}


@app.get("/api/v1/funnel")
async def get_conversion_funnel(
    period_days: int = Query(default=7, ge=1, le=30),
    platform: Optional[str] = Query(default=None, enum=["ios", "android", "web"]),
):
    """E-commerce conversion funnel metrics."""
    views = random.randint(50000, 200000)
    searches = int(views * random.uniform(0.4, 0.6))
    pdp_views = int(views * random.uniform(0.3, 0.5))
    add_to_cart = int(pdp_views * random.uniform(0.15, 0.30))
    checkout = int(add_to_cart * random.uniform(0.5, 0.75))
    purchased = int(checkout * random.uniform(0.65, 0.90))

    return {
        "data": {
            "platform": platform or "all",
            "period_days": period_days,
            "funnel": [
                {"stage": "Sessions", "count": views, "drop_off_pct": 0},
                {"stage": "Search / Browse", "count": searches,
                 "drop_off_pct": round((views - searches) / views * 100, 1)},
                {"stage": "Product Page View", "count": pdp_views,
                 "drop_off_pct": round((searches - pdp_views) / searches * 100, 1)},
                {"stage": "Add to Cart", "count": add_to_cart,
                 "drop_off_pct": round((pdp_views - add_to_cart) / pdp_views * 100, 1)},
                {"stage": "Checkout", "count": checkout,
                 "drop_off_pct": round((add_to_cart - checkout) / add_to_cart * 100, 1)},
                {"stage": "Purchased", "count": purchased,
                 "drop_off_pct": round((checkout - purchased) / checkout * 100, 1)},
            ],
            "overall_conversion_rate": round(purchased / views * 100, 2),
        },
        "source": "ecomm_ads.fact_user_events",
    }


# ── WebSocket: Live Orders ─────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, msg: dict):
        for ws in self.active[:]:
            try:
                await ws.send_json(msg)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


@app.websocket("/ws/live-orders")
async def websocket_live_orders(websocket: WebSocket):
    """Stream real-time order events via WebSocket."""
    await manager.connect(websocket)
    cities = ["Bangkok", "Chiang Mai", "Phuket", "Pattaya", "Khon Kaen"]
    statuses = ["pending", "confirmed", "shipped", "delivered"]
    try:
        while True:
            event = {
                "type": "order_event",
                "order_id": random.randint(10000, 99999),
                "status": random.choice(statuses),
                "amount": round(random.uniform(150, 8000), 2),
                "city": random.choice(cities),
                "payment_method": random.choice(["cod", "credit_card", "wallet"]),
                "ts": datetime.utcnow().isoformat(),
            }
            await manager.broadcast(event)
            await asyncio.sleep(random.uniform(0.5, 2.0))
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
