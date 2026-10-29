# Day 3: Spreadsheets Mastery - Pivot Tables, Lookups, Data Cleaning
## Google Data Analyst Interview Prep - Week 1

---

### 🎯 Learning Objectives
By end of Day 3, you can:
- [ ] Build complex pivot tables with calculated fields, grouping, slicers
- [ ] Master VLOOKUP, XLOOKUP, INDEX/MATCH for flexible lookups
- [ ] Clean messy data: text functions, date parsing, deduplication
- [ ] Create dashboard-style reports with conditional formatting, charts
- [ ] Complete 5 real-world cleaning/analysis exercises in <90 minutes

---

### 📖 Core Concepts Reference

#### Pivot Table Power Features

**Calculated Fields (Insert → Pivot Table → Analyze → Fields, Items & Sets)**
```excel
-- Revenue per Unit
=Revenue / Units_Sold

-- Profit Margin
=(Revenue - Cost) / Revenue

-- YoY Growth (requires grouped dates)
=(Current_Year - Prior_Year) / Prior_Year

-- Conditional Bucketing
=IF(Revenue > 10000, "High", IF(Revenue > 5000, "Medium", "Low"))
```

**Grouping (Right-click on date/number field)**
- Dates: Seconds → Minutes → Hours → Days → Months → Quarters → Years
- Numbers: Custom bins (e.g., 0-10, 10-50, 50-100, 100+)

**Show Values As (Right-click value → Show Values As)**
- % of Grand Total
- % of Column/Row Total
- % of Parent Row/Column
- Running Total In...
- Difference From... (previous/next)
- Rank (Largest to Smallest / Smallest to Largest)
- Index

**Slicers & Timelines (Insert → Slicer/Timeline)**
- Visual filters for dashboards
- Connect multiple pivot tables to one slicer

#### Lookup Functions Comparison

| Function | Syntax | Best For | Google Sheets | Excel |
|----------|--------|----------|---------------|-------|
| **VLOOKUP** | `=VLOOKUP(key, range, index, [sorted])` | Simple left-to-right | ✅ | ✅ |
| **XLOOKUP** | `=XLOOKUP(key, lookup_range, return_range, [not_found], [match_mode], [search_mode])` | Modern, flexible, exact match default | ✅ | ✅ (365) |
| **INDEX/MATCH** | `=INDEX(return_range, MATCH(key, lookup_range, 0))` | Large datasets, left lookup, multiple criteria | ✅ | ✅ |
| **FILTER** | `=FILTER(return_range, condition_range=key)` | Multiple matches, dynamic arrays | ✅ | ✅ (365) |

**XLOOKUP - The Modern Standard**
```excel
-- Basic exact match (default)
=XLOOKUP(A2, customers[ID], customers[Name])

-- Return multiple columns
=XLOOKUP(A2, customers[ID], customers[Name:Email])

-- With default if not found
=XLOOKUP(A2, products[SKU], products[Price], "Not Found")

-- Horizontal lookup (replaces HLOOKUP)
=XLOOKUP("Q1", headers[1:1], data[2:100])

-- Multiple criteria (helper column or boolean multiplication)
=XLOOKUP(1, (A:A=A2)*(B:B=B2), C:C)
```

#### Data Cleaning Toolkit

**Text Functions**
```excel
-- Trim whitespace
=TRIM(A2)

-- Remove non-printable chars
=CLEAN(A2)

-- Standardize case
=PROPER(TRIM(A2))    -- Proper Case
=UPPER(TRIM(A2))     -- UPPERCASE
=LOWER(TRIM(A2))     -- lowercase

-- Extract parts
=LEFT(A2, FIND("@", A2)-1)      -- Before @
=MID(A2, FIND(" ", A2)+1, 50)   -- Middle
=RIGHT(A2, LEN(A2)-FIND("@",A2)) -- After @

-- Replace/Substitute
=SUBSTITUTE(A2, "old", "new")        -- All occurrences
=REPLACE(A2, 1, 3, "NEW")            -- Position-based
=REGEXREPLACE(A2, "\D", "")          -- Keep only digits (Sheets)
```

**Date Parsing (Critical for Google Interviews)**
```excel
-- Text to Date (common formats)
=DATEVALUE("Jan 15, 2024")
=DATEVALUE("2024-01-15")
=DATEVALUE("01/15/2024")

-- Parse custom formats
=DATE(
  RIGHT(A2,4),           -- Year
  MID(A2,4,2),           -- Month
  LEFT(A2,2)             -- Day
)  -- For "DD/MM/YYYY"

-- Date components
=YEAR(A2), MONTH(A2), DAY(A2)
=WEEKDAY(A2)             -- 1=Sun...7=Sat
=WEEKNUM(A2)             -- Week of year
=EOMONTH(A2,0)           -- End of month
=EDATE(A2, -1)           -- Previous month

-- Date math
=A2 - B2                 -- Days difference
=DATEDIF(A2, B2, "d")    -- Days
=DATEDIF(A2, B2, "m")    -- Months
=DATEDIF(A2, B2, "y")    -- Years
```

**Deduplication**
```excel
-- Highlight duplicates (Conditional Formatting)
=COUNTIF($A$2:$A$100, A2) > 1

-- Remove duplicates: Data → Remove Duplicates

-- Formula approach (keep first)
=IF(COUNTIF($A$2:A2, A2)=1, "Keep", "Duplicate")

-- Advanced: deduplicate by multiple columns
=IF(COUNTIFS($A$2:A2, A2, $B$2:B2, B2)=1, "Keep", "Duplicate")
```

**Handling Errors**
```excel
=IFERROR(VLOOKUP(...), "Not Found")
=IFNA(XLOOKUP(...), "Missing")
=ISERROR(A2), ISNA(A2), ISBLANK(A2)
```

---

### 💪 Practice Exercises (Real-World Scenarios)

#### Exercise 1: Sales Dashboard (Pivot Mastery)
**Data:** `sales_raw.csv` - 5000 rows: Date, Rep, Region, Product, Category, Units, Unit_Price, Discount

**Tasks:**
1. Create pivot: **Revenue by Region × Quarter** with % of Grand Total
2. Create pivot: **Top 5 Reps by Revenue** with Running Total %
3. Create pivot: **Product Category Performance** - Revenue, Units, Avg Price, Margin%
4. Add **Slicers** for Year and Region (connect all pivots)
5. Build **Dashboard Sheet** with 4 charts + KPIs

**Expected Time:** 25 min

---

#### Exercise 2: Customer Merge (Lookup Mastery)
**Data:**
- `customers.csv` - 2000 rows: Customer_ID, Name, Email, Signup_Date, Tier
- `orders.csv` - 10000 rows: Order_ID, Customer_ID, Product, Amount, Date
- `support_tickets.csv` - 500 rows: Ticket_ID, Customer_Email, Issue, Status, Resolution_Time

**Tasks:**
1. **VLOOKUP/XLOOKUP:** Add Customer Name & Tier to orders table
2. **INDEX/MATCH:** Add Signup_Date to support_tickets using Email (not ID)
3. **FILTER/XLOOKUP multi:** Find all orders for customers with "Enterprise" tier
4. **Reconcile:** Find customers in orders but NOT in customers table (data quality)
5. **Calculate:** Days from signup to first order per customer

**Expected Time:** 30 min

---

#### Exercise 3: Messy Data Cleanup (Cleaning Mastery)
**Data:** `dirty_leads.csv` - 1000 rows with issues:
- Names: "  john SMITH  ", "Jane Doe", "BOB JONES"
- Emails: "john@email.com ", "JANE@EMAIL.COM", "bob@email", "invalid"
- Phones: "555-123-4567", "(555) 123-4567", "5551234567", "+1 555 123 4567"
- Dates: "1/15/24", "2024-01-15", "Jan 15 2024", "15-Jan-24"
- Company: "Google Inc.", "GOOGLE", "google", "Alphabet (Google)"

**Tasks:**
1. **Standardize Names:** Proper case, trimmed
2. **Standardize Emails:** Lowercase, trimmed, validate format (contains @ and .)
3. **Standardize Phones:** Format as (555) 123-4567
4. **Parse Dates:** Convert all to YYYY-MM-DD
5. **Fuzzy Match Companies:** Group "Google" variants → "Google"
6. **Flag Issues:** Column with "✓ Clean" or "⚠ Issue: [details]"

**Expected Time:** 25 min

---

#### Exercise 4: Cohort Analysis (Advanced Pivot + Formulas)
**Data:** `user_activity.csv` - 10000 rows: User_ID, Event_Date, Event_Type (signup, login, purchase, churn)

**Tasks:**
1. Determine **cohort month** for each user (first signup date)
2. For each cohort, calculate **Week 1, Week 2, Week 3, Week 4 retention**
3. Build **Retention Heatmap** pivot: Cohort Month × Week Number = % Retained
4. Add **Conditional Formatting** color scale (red → green)
5. Calculate **Average Revenue Per User (ARPU)** per cohort at Week 4

**Expected Time:** 30 min

---

#### Exercise 5: Executive Summary Dashboard (Integration)
**Data:** Combination of above datasets

**Tasks:**
1. **KPI Row:** Total Revenue, Total Users, Avg Order Value, Churn Rate, MoM Growth
2. **Trend Chart:** Monthly Revenue (12 months) with 3-month moving average line
3. **Breakdown:** Revenue by Channel (pivot + pie/bar)
4. **Top/Bottom:** Top 10 Customers, Bottom 10 Products
5. **Alert Section:** Conditional formatting - metrics below threshold highlighted red
6. **Dynamic:** All updates when raw data refreshes

**Expected Time:** 30 min

---

### ⚡ Google Interview Spreadsheet Patterns

#### Pattern 1: "Dynamic Named Ranges" (Sheets: Named Ranges + INDIRECT)
```excel
-- Create named range "SalesData" = OFFSET(Sheet1!$A$1,0,0,COUNTA(Sheet1!$A:$A),10)
-- Pivot tables auto-expand when data grows
```

#### Pattern 2: "Array Formulas for Bulk Operations" (Sheets: ARRAYFORMULA)
```excel
-- Apply to entire column without dragging
=ARRAYFORMULA(IF(A2:A="", "", PROPER(TRIM(A2:A))))

-- VLOOKUP entire column
=ARRAYFORMULA(IFERROR(VLOOKUP(A2:A, Lookup!$A:$B, 2, FALSE)))
```

#### Pattern 3: "QUERY Function" (Google Sheets Superpower)
```excel
-- SQL-like queries on spreadsheet data
=QUERY(A:E, "SELECT B, SUM(E) WHERE A > date '2024-01-01' GROUP BY B ORDER BY SUM(E) DESC LABEL SUM(E) 'Total Revenue'", 1)

-- Pivot within QUERY
=QUERY(A:E, "SELECT A, SUM(E) WHERE B='West' GROUP BY A PIVOT C", 1)
```

#### Pattern 4: "Conditional Aggregation without Pivot"
```excel
-- SUMIFS/COUNTIFS/AVERAGEIFS for dashboard metrics
=SUMIFS(Revenue_Range, Region_Range, "West", Date_Range, ">="&DATE(2024,1,1), Date_Range, "<="&DATE(2024,3,31))

-- COUNTUNIQUEIFS (Sheets only)
=COUNTUNIQUEIFS(User_ID_Range, Date_Range, ">="&TODAY()-30)
```

---

### 🏋️ Day 3 Practice Routine

| Time | Activity |
|------|----------|
| 0:00-0:20 | Review function syntax, practice XLOOKUP variants |
| 0:20-1:20 | Complete Exercises 1-3 (core skills) |
| 1:20-2:00 | Complete Exercises 4-5 (integration) |
| 2:00-2:30 | Build one dashboard from scratch without reference |
| 2:30-3:00 | Practice explaining your approach out loud |

---

### ✅ Day 3 Completion Checklist
- [ ] Pivot tables: calculated fields, grouping, show values as, slicers
- [ ] XLOOKUP: exact, approximate, multi-column, horizontal, not_found
- [ ] INDEX/MATCH: left lookup, multiple criteria
- [ ] Text cleaning: TRIM, PROPER, SUBSTITUTE, REGEXREPLACE
- [ ] Date parsing: multiple formats → standard YYYY-MM-DD
- [ ] Deduplication: highlight, formula, remove
- [ ] QUERY function (Sheets) for SQL-like analysis
- [ ] Dashboard: KPIs, charts, conditional formatting, dynamic ranges

---

### 📝 Notes Space
```
Functions I need more practice with:
______________________________________________________________________________

Cleaning patterns that appear often:
______________________________________________________________________________

Dashboard design tips:
______________________________________________________________________________
```

---

### 🔗 Resources
- [Google Sheets Function List](https://support.google.com/docs/table/25273?hl=en)
- [Excel Jet - Formula Examples](https://exceljet.net/formulas)
- [Pivot Table Guide](https://support.google.com/docs/answer/1272900?hl=en)
- [Ben Collins - Sheets Tips](https://www.benlcollins.com/spreadsheets/)

---

*Next: DAY_4_TABLEAU.md - Visualizations, calculated fields, dashboards, LOD expressions*