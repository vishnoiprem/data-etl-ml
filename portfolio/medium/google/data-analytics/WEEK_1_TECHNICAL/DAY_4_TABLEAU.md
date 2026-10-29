# Day 4: Tableau Mastery - Visualizations, Calculations, Dashboards
## Google Data Analyst Interview Prep - Week 1

---

### 🎯 Learning Objectives
By end of Day 4, you can:
- [ ] Build core chart types: bar, line, scatter, histogram, heatmap, treemap, bullet, waterfall
- [ ] Write calculated fields: LOD expressions, table calculations, date logic, string parsing
- [ ] Design interactive dashboards: actions, parameters, tooltips, navigation
- [ ] Publish to Tableau Public / Server with proper formatting
- [ ] Complete 3 portfolio-ready dashboard projects in <3 hours

---

### 📖 Core Concepts Reference

#### Chart Type Selection Guide

| Business Question | Best Chart | Alternative |
|-------------------|------------|-------------|
| Compare categories | Bar (horizontal) | Treemap |
| Trend over time | Line | Area |
| Distribution | Histogram / Box Plot | Density |
| Part-to-whole | Stacked Bar / Treemap | Pie (avoid) |
| Correlation | Scatter Plot | Heatmap |
| Ranking | Bar + Reference Line | Bullet Chart |
| KPI vs Target | Bullet / Gauge | Big Number + Trend |
| Geo data | Filled Map / Symbol Map | — |
| Hierarchical | Treemap / Sunburst | — |
| Flow / Funnel | Sankey / Funnel Chart | Waterfall |

#### Calculated Fields Syntax

**Basic**
```tableau
-- String
CONTAINS([Product Name], "Pro")
REPLACE([Category], "Old", "New")
LEFT([Order ID], 4)  -- Year extraction

-- Date
DATETRUNC('month', [Order Date])
DATEADD('day', 7, [Ship Date])
DATEDIFF('day', [Order Date], [Ship Date])
YEAR([Order Date])

-- Logic
IF [Profit] > 0 THEN "Profitable" ELSE "Loss" END
CASE [Region] WHEN "West" THEN 1 WHEN "East" THEN 2 ELSE 3 END
IIF([Sales] > 1000, "High", "Low")

-- Aggregation (must wrap in ATTR or use in viz)
SUM([Sales]) / SUM([Quantity])  -- Avg price per unit
```

#### Level of Detail (LOD) Expressions — **Critical for Google**

**FIXED** — Compute at specified dimension, ignore viz filters
```tableau
-- Customer Lifetime Value (fixed per customer, ignores date filter)
{ FIXED [Customer ID] : SUM([Sales]) }

-- Cohort size (fixed per cohort)
{ FIXED [Cohort Month] : COUNTD([Customer ID]) }

-- First order date per customer
{ FIXED [Customer ID] : MIN([Order Date]) }
```

**INCLUDE** — Compute at viz level + additional dimensions
```tableau
-- Average order value per customer (then avg across customers in viz)
{ INCLUDE [Customer ID] : SUM([Sales]) }  -- Per customer total
AVG({ INCLUDE [Customer ID] : SUM([Sales]) })  -- Avg of customer totals
```

**EXCLUDE** — Compute at viz level minus specified dimensions
```tableau
-- % of total region sales (exclude state from Region-level viz)
SUM([Sales]) / SUM({ EXCLUDE [State] : SUM([Sales]) })
```

#### Table Calculations (Compute Using)

| Function | Use Case | Compute Using |
|----------|----------|---------------|
| `RUNNING_SUM()` | Cumulative totals | Table Across / Pane Down |
| `RUNNING_AVG()` | Moving average | Table Across |
| `WINDOW_SUM()` | Flexible window | Custom |
| `LOOKUP()` | Compare to previous/next | Table Across |
| `INDEX()` / `SIZE()` | Ranking, pagination | Table Down |
| `FIRST()` / `LAST()` | Filter first/last N | Table Across |
| `TOTAL()` | Grand total in context | Table Across |
| `RANK()` / `RANK_DENSE()` | Ranking | Table Down |
| `PERCENTILE()` | Percentile bands | Table Down |

**Moving Average (3-month)**
```tableau
WINDOW_AVG(SUM([Sales]), -2, 0)  -- Current + 2 prior
```

**Percent of Total**
```tableau
SUM([Sales]) / TOTAL(SUM([Sales]))
```

**Year-over-Year Growth**
```tableau
(SUM([Sales]) - LOOKUP(SUM([Sales]), -12)) / ABS(LOOKUP(SUM([Sales]), -12))
```

---

### 🎨 Dashboard Design Principles (Google Style)

#### Layout Structure
```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: Title | Last Updated | Data Source | Filters       │
├──────────────┬──────────────────────────────┬────────────────┤
│  KPI ROW     │  MAIN VISUALIZATION          │  SIDE PANEL    │
│  (4-5 big    │  (Primary chart - large,     │  (Filters,     │
│   numbers)   │   interactive, drives other  │   parameters,  │
│              │   charts via actions)        │   legends)     │
├──────────────┼──────────────────────────────┼────────────────┤
│  SUPPORTING  │  SECONDARY VISUALIZATIONS    │  DETAIL /      │
│  CHARTS      │  (Drill-downs, breakdowns)   │  DATA TABLE    │
│  (2-3 small) │                              │  (On demand)   │
└──────────────┴──────────────────────────────┴────────────────┘
```

#### Color Palette (Google Material)
- **Primary:** #1A73E8 (Blue), #34A853 (Green), #EA4335 (Red), #FBBC05 (Yellow)
- **Neutral:** #202124 (Dark), #5F6368 (Gray), #FFFFFF (White), #F1F3F4 (Light BG)
- **Sequential:** Blues (low→high), **Diverging:** Blue-White-Red

#### Interactivity
- **Filter Actions:** Click bar → filters other sheets
- **Highlight Actions:** Hover → highlights related marks
- **URL Actions:** Click → opens external link (record detail)
- **Parameter Actions:** Click → updates parameter (dynamic measures)
- **Set Actions:** Click → adds to set (drill-down)

---

### 💪 Practice Projects (Build in Order)

#### Project 1: Executive Sales Dashboard (2 hours)
**Data:** Superstore or similar (Orders, Returns, People)

**Requirements:**
1. **KPI Row:** Total Sales, Total Profit, Profit Margin, YoY Growth, Avg Order Value
2. **Main Viz:** Sales Trend (Monthly, dual-axis with Profit Margin %)
3. **Supporting:**
   - Sales by Region (Map + Bar)
   - Top 10 Customers (Bar with reference line for avg)
   - Category/Sub-Category Treemap (Size=Sales, Color=Profit)
4. **Interactivity:**
   - Region filter (map click filters all)
   - Year parameter (2021/2022/2023/All)
   - Category highlight action
5. **Formatting:** Google colors, tooltips with context, clean typography

**Deliverable:** Published to Tableau Public, link ready to share

---

#### Project 2: Customer Cohort Retention Dashboard (1.5 hours)
**Data:** User events (User_ID, Event_Date, Event_Type, Revenue)

**Requirements:**
1. **Data Prep (in Tableau):**
   - Cohort Month: `DATETRUNC('month', {FIXED [User ID] : MIN([Event Date])})`
   - Period Number: `DATEDIFF('month', [Cohort Month], DATETRUNC('month', [Event Date]))`
   - Retained Flag: `COUNTD([User ID])` per cohort/period
2. **Main Viz:** Retention Heatmap (Cohort Month × Period Number, Color = % Retained)
2. **Supporting:**
   - Cohort Size bar chart
   - Revenue per Cohort line chart
   - Period 0 vs Period 1 comparison (waterfall)
3. **Interactivity:** Cohort selector parameter, hover tooltip with exact counts

**Deliverable:** Published, demonstrates LOD + Table Calculations mastery

---

#### Project 3: Product Analytics Funnel Dashboard (1 hour)
**Data:** E-commerce events (Session_ID, User_ID, Timestamp, Event: view/cart/checkout/purchase, Product, Category, Price)

**Requirements:**
1. **Funnel Chart:** View → Cart → Checkout → Purchase (conversion % at each step)
2. **Drop-off Analysis:** Bar chart showing drop-off count by step
3. **Segmentation:** Funnel by Device, Channel, New vs Returning (parameter)
4. **Product Detail:** Top converting products, revenue by category
5. **Calculated Fields:**
   - Conversion Rate: `COUNTD(IF [Event]='Purchase' THEN [Session_ID] END) / COUNTD([Session_ID])`
   - Cart Abandonment: `1 - (Checkout / Cart)`

**Deliverable:** Published, shows parameter-driven segmentation

---

### ⚡ Google Interview Tableau Patterns

#### Pattern 1: "Dynamic Measure Selection"
```tableau
-- Parameter: [Select Measure] with values: "Sales", "Profit", "Quantity", "Orders"
-- Calculated Field: [Dynamic Measure]
CASE [Select Measure]
  WHEN "Sales" THEN SUM([Sales])
  WHEN "Profit" THEN SUM([Profit])
  WHEN "Quantity" THEN SUM([Quantity])
  WHEN "Orders" THEN COUNTD([Order ID])
END

-- Use [Dynamic Measure] everywhere in viz
-- Parameter action: Click KPI card → updates parameter
```

#### Pattern 2: "Drill-Down with Set Actions"
```tableau
-- Create Set: [Category Set] on [Category]
-- Set Action: Click category bar → Add to [Category Set]
-- Calculated Field: [Drill Level]
IF [Category Set] THEN [Sub-Category] ELSE [Category] END

-- Use [Drill Level] on Rows, shows Category normally, Sub-Category when selected
```

#### Pattern 3: "Comparison to Benchmark"
```tableau
-- Parameter: [Benchmark Type] = "Average", "Median", "Top Quartile", "Target"
-- Reference Line: Dynamic based on parameter
CASE [Benchmark Type]
  WHEN "Average" THEN WINDOW_AVG(SUM([Sales]))
  WHEN "Median" THEN WINDOW_MEDIAN(SUM([Sales]))
  WHEN "Top Quartile" THEN WINDOW_PERCENTILE(SUM([Sales]), 0.75)
  WHEN "Target" THEN [Target Parameter]
END
```

#### Pattern 4: "Mobile-Optimized Layout"
- Dashboard size: **Phone (375×667)** or **Tablet (768×1024)**
- Vertical stack, large touch targets
- Minimize filters, use parameter buttons
- Test: Tableau Public → "Open on Mobile"

---

### 🏋️ Day 4 Practice Routine

| Time | Activity |
|------|----------|
| 0:00-0:30 | Review LOD syntax, table calc "Compute Using" options |
| 0:30-2:00 | Build Project 1 (Executive Dashboard) |
| 2:00-3:00 | Build Project 2 (Cohort Retention) |
| 3:00-3:30 | Build Project 3 (Funnel) |
| 3:30-4:00 | Publish all 3, test interactivity, refine tooltips |

---

### ✅ Day 4 Completion Checklist
- [ ] All chart types built from memory
- [ ] LOD expressions: FIXED, INCLUDE, EXCLUDE written without reference
- [ ] Table calculations: RUNNING_, WINDOW_, LOOKUP, RANK, TOTAL
- [ ] Parameters: string, integer, date, calculated field driven
- [ ] Dashboard actions: filter, highlight, URL, parameter, set
- [ ] 3 published dashboards on Tableau Public
- [ ] Can explain design choices: "Why this chart?" "Why this color?"

---

### 📝 Notes Space
```
LOD expressions that tripped me up:
______________________________________________________________________________

Table calc "Compute Using" scenarios:
______________________________________________________________________________

Dashboard design decisions to remember:
______________________________________________________________________________
```

---

### 🔗 Resources
- [Tableau Calculation Reference](https://help.tableau.com/current/pro/desktop/en-us/functions.htm)
- [LOD Expressions Deep Dive](https://www.tableau.com/learn/articles/level-detail-expressions)
- [Tableau Public Gallery](https://public.tableau.com/en-us/s/gallery) — study top vizzes
- [Google Material Design Color](https://material.io/design/color/)

---

*Next: DAY_5_PYTHON.md - Pandas, NumPy, visualization, EDA workflow*