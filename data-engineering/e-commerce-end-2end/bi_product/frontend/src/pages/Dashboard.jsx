/**
 * E-Commerce BI Dashboard - Main Page
 * Stack: React + Recharts + Tailwind CSS
 * Real-time updates via WebSocket
 */
import React, { useState, useEffect, useCallback } from "react";
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, FunnelChart, Funnel, LabelList,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1";
const WS_URL = process.env.REACT_APP_WS_URL || "ws://localhost:8000/ws/live-orders";

const COLORS = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

// ── Utility ───────────────────────────────────────────────────
const fmt = (n) => new Intl.NumberFormat("th-TH").format(Math.round(n));
const fmtCcy = (n) => `฿${fmt(n)}`;
const fmtPct = (n) => `${n}%`;

// ── KPI Card ──────────────────────────────────────────────────
const KPICard = ({ title, value, change, subtitle, color = "indigo" }) => {
  const isPos = change >= 0;
  return (
    <div className={`bg-white rounded-2xl shadow-sm border border-gray-100 p-6`}>
      <p className="text-sm text-gray-500 font-medium">{title}</p>
      <p className={`text-3xl font-bold mt-1 text-${color}-600`}>{value}</p>
      {change !== undefined && (
        <p className={`text-sm mt-1 font-medium ${isPos ? "text-emerald-500" : "text-red-500"}`}>
          {isPos ? "▲" : "▼"} {Math.abs(change)}% vs yesterday
        </p>
      )}
      {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
    </div>
  );
};

// ── Section Header ────────────────────────────────────────────
const SectionHeader = ({ title, subtitle }) => (
  <div className="mb-4">
    <h2 className="text-xl font-bold text-gray-800">{title}</h2>
    {subtitle && <p className="text-sm text-gray-400 mt-0.5">{subtitle}</p>}
  </div>
);

// ── Live Order Ticker ─────────────────────────────────────────
const LiveOrderTicker = ({ orders }) => (
  <div className="bg-gray-900 rounded-2xl p-4 h-48 overflow-y-auto">
    <p className="text-xs text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
      <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse inline-block" />
      Live Orders
    </p>
    {orders.map((o, i) => (
      <div key={i} className="flex items-center justify-between py-1 border-b border-gray-800 text-sm">
        <span className="text-gray-300">#{o.order_id}</span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
          o.status === "delivered" ? "bg-emerald-900 text-emerald-300" :
          o.status === "shipped" ? "bg-blue-900 text-blue-300" :
          o.status === "confirmed" ? "bg-yellow-900 text-yellow-300" :
          "bg-gray-700 text-gray-300"
        }`}>{o.status}</span>
        <span className="text-indigo-400 font-semibold">{fmtCcy(o.amount)}</span>
        <span className="text-gray-500 text-xs">{o.city}</span>
      </div>
    ))}
  </div>
);

// ── RFM Segment Pie ───────────────────────────────────────────
const RFMPieChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <PieChart>
      <Pie
        data={data}
        dataKey="customer_count"
        nameKey="segment"
        cx="50%" cy="50%"
        outerRadius={110}
        label={({ segment, percentage }) => `${segment} ${percentage}%`}
        labelLine={false}
      >
        {data.map((_, i) => (
          <Cell key={i} fill={COLORS[i % COLORS.length]} />
        ))}
      </Pie>
      <Tooltip formatter={(v) => [fmt(v), "Customers"]} />
    </PieChart>
  </ResponsiveContainer>
);

// ── Funnel Chart ──────────────────────────────────────────────
const ConversionFunnel = ({ data }) => (
  <div className="space-y-2">
    {data.map((stage, i) => {
      const pct = Math.round(stage.count / data[0].count * 100);
      return (
        <div key={i}>
          <div className="flex justify-between text-sm mb-1">
            <span className="font-medium text-gray-700">{stage.stage}</span>
            <span className="text-gray-500">{fmt(stage.count)} ({pct}%)</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-6">
            <div
              className="h-6 rounded-full flex items-center justify-end pr-2"
              style={{
                width: `${pct}%`,
                backgroundColor: COLORS[i],
                transition: "width 0.5s ease",
              }}
            >
              {stage.drop_off_pct > 0 && (
                <span className="text-white text-xs">-{stage.drop_off_pct}%</span>
              )}
            </div>
          </div>
        </div>
      );
    })}
  </div>
);

// ── Warehouse Grid ────────────────────────────────────────────
const WarehouseCard = ({ wh }) => {
  const statusColor = {
    ok: "border-emerald-400",
    warning: "border-amber-400",
    low: "border-blue-400",
  }[wh.status] || "border-gray-300";

  return (
    <div className={`bg-white rounded-xl p-4 border-l-4 shadow-sm ${statusColor}`}>
      <div className="flex justify-between items-start">
        <div>
          <p className="font-bold text-gray-800">{wh.warehouse_code}</p>
          <p className="text-xs text-gray-400">{wh.city}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
          wh.status === "ok" ? "bg-emerald-100 text-emerald-700" :
          wh.status === "warning" ? "bg-amber-100 text-amber-700" :
          "bg-blue-100 text-blue-700"
        }`}>{wh.status.toUpperCase()}</span>
      </div>
      <div className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Utilization</span>
          <span className={`font-semibold ${wh.capacity_utilization_pct > 90 ? "text-amber-600" : "text-gray-700"}`}>
            {wh.capacity_utilization_pct}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Stockouts</span>
          <span className={`font-semibold ${wh.stockout_skus > 20 ? "text-red-500" : "text-gray-700"}`}>
            {wh.stockout_skus} SKUs
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Avg Delivery</span>
          <span className="font-semibold text-gray-700">{wh.avg_delivery_days}d</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Inventory Value</span>
          <span className="font-semibold text-indigo-600">{fmtCcy(wh.inventory_value)}</span>
        </div>
      </div>
    </div>
  );
};


// ══════════════════════════════════════════════════════════════
// MAIN DASHBOARD
// ══════════════════════════════════════════════════════════════
export default function Dashboard() {
  const [kpi, setKpi] = useState({});
  const [gmv, setGmv] = useState([]);
  const [products, setProducts] = useState([]);
  const [rfm, setRfm] = useState([]);
  const [funnel, setFunnel] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [liveOrders, setLiveOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  // ── Fetch data ──────────────────────────────────────────────
  const fetchAll = useCallback(async () => {
    try {
      const [kpiRes, gmvRes, prodRes, rfmRes, funnelRes, whRes] = await Promise.all([
        fetch(`${API}/kpi/summary`).then(r => r.json()),
        fetch(`${API}/gmv/daily?days=30`).then(r => r.json()),
        fetch(`${API}/products/top?limit=10`).then(r => r.json()),
        fetch(`${API}/customers/rfm`).then(r => r.json()),
        fetch(`${API}/funnel`).then(r => r.json()),
        fetch(`${API}/warehouse/status`).then(r => r.json()),
      ]);
      setKpi(kpiRes.data);
      setGmv(gmvRes.data);
      setProducts(prodRes.data);
      setRfm(rfmRes.data);
      setFunnel(funnelRes.data?.funnel || []);
      setWarehouses(whRes.data);
      setLoading(false);
    } catch (e) {
      console.error("API error:", e);
    }
  }, []);

  // ── WebSocket ───────────────────────────────────────────────
  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 60000); // refresh every 60s

    const ws = new WebSocket(WS_URL);
    ws.onmessage = (e) => {
      const order = JSON.parse(e.data);
      setLiveOrders(prev => [order, ...prev].slice(0, 20));
    };
    ws.onerror = () => console.warn("WebSocket unavailable");

    return () => {
      clearInterval(interval);
      ws.close();
    };
  }, [fetchAll]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto" />
          <p className="mt-4 text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const TABS = ["overview", "products", "customers", "operations"];

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10 shadow-sm">
        <div className="max-w-screen-2xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center">
              <span className="text-white font-bold text-lg">E</span>
            </div>
            <div>
              <h1 className="text-lg font-bold text-gray-900">EComm Intelligence</h1>
              <p className="text-xs text-gray-400">Powered by Azure + Databricks + ClickHouse</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            Live · Updated {new Date().toLocaleTimeString()}
          </div>
        </div>
      </header>

      <main className="max-w-screen-2xl mx-auto px-6 py-6 space-y-8">
        {/* Tab Navigation */}
        <div className="flex gap-1 bg-gray-100 p-1 rounded-xl w-fit">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all ${
                activeTab === tab
                  ? "bg-white text-indigo-600 shadow-sm"
                  : "text-gray-500 hover:text-gray-700"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* ── OVERVIEW TAB ───────────────────────────────────── */}
        {activeTab === "overview" && (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-4">
              <KPICard title="GMV Today" value={fmtCcy(kpi.gmv_today)} change={5.2} color="indigo" />
              <KPICard title="Orders Today" value={fmt(kpi.orders_today)} change={3.1} color="cyan" />
              <KPICard title="Unique Buyers" value={fmt(kpi.unique_buyers_today)} change={-1.4} color="violet" />
              <KPICard title="Avg Order Value" value={fmtCcy(kpi.avg_order_value)} change={2.8} color="emerald" />
              <KPICard title="Completion Rate" value={fmtPct(kpi.completion_rate_pct)} subtitle="vs 91% yesterday" color="emerald" />
              <KPICard title="Platform Revenue" value={fmtCcy(kpi.platform_revenue_today)} change={4.5} color="amber" />
            </div>

            {/* GMV Trend + Live Orders */}
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
                <SectionHeader title="GMV Trend (30 Days)" subtitle="Gross Merchandise Value" />
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={gmv}>
                    <defs>
                      <linearGradient id="gmvGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={d => d.slice(5)} />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `฿${(v / 1000).toFixed(0)}k`} />
                    <Tooltip formatter={(v) => [fmtCcy(v), "GMV"]} />
                    <Area type="monotone" dataKey="gmv" stroke="#6366f1" fill="url(#gmvGrad)" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div>
                <SectionHeader title="Live Order Stream" />
                <LiveOrderTicker orders={liveOrders} />
              </div>
            </div>
          </>
        )}

        {/* ── PRODUCTS TAB ───────────────────────────────────── */}
        {activeTab === "products" && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <SectionHeader title="Top 10 Products by Revenue" />
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={products} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `฿${(v/1000).toFixed(0)}k`} />
                  <YAxis type="category" dataKey="product_name" width={130} tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [fmtCcy(v), "Revenue"]} />
                  <Bar dataKey="total_revenue" fill="#6366f1" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <SectionHeader title="Conversion Funnel" subtitle="All platforms · Last 7 days" />
              <ConversionFunnel data={funnel} />
            </div>
          </div>
        )}

        {/* ── CUSTOMERS TAB ─────────────────────────────────── */}
        {activeTab === "customers" && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <SectionHeader title="Customer RFM Segments" />
              <RFMPieChart data={rfm} />
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <SectionHeader title="Segment Details" />
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b">
                      <th className="pb-2">Segment</th>
                      <th className="pb-2">Customers</th>
                      <th className="pb-2">Avg Value</th>
                      <th className="pb-2">Avg Freq.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rfm.map((r, i) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 font-medium flex items-center gap-2">
                          <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                          {r.segment}
                        </td>
                        <td className="py-2">{fmt(r.customer_count)}</td>
                        <td className="py-2">{fmtCcy(r.avg_monetary)}</td>
                        <td className="py-2">{r.avg_frequency}x</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ── OPERATIONS TAB ────────────────────────────────── */}
        {activeTab === "operations" && (
          <>
            <SectionHeader title="Warehouse Status" subtitle="Inventory & fulfillment metrics by warehouse" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
              {warehouses.map((wh, i) => (
                <WarehouseCard key={i} wh={wh} />
              ))}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
