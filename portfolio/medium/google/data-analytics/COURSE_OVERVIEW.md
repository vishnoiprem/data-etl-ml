# Google Data Analyst Interview Prep Course
## 2-Week Intensive Program

---

### 🎯 Course Objective
Prepare comprehensively for Google Data Analyst interviews (including Google Data Analytics Certificate capstone roles) in 14 days with focused, high-yield content.

---

### 📅 Course Structure

| Week | Focus | Days |
|------|-------|------|
| **Week 1** | Core Technical Foundations | Day 1-7 |
| **Week 2** | Applied Skills & Interview Mastery | Day 8-14 |

---

### 📚 Weekly Breakdown

#### **Week 1: Technical Foundations (Days 1-7)**

| Day | Topic | Hours | Deliverable |
|-----|-------|-------|-------------|
| **Day 1** | SQL Mastery - Queries, Joins, Aggregations | 3-4 | 20 practice queries |
| **Day 2** | SQL Advanced - Window Functions, CTEs, Optimization | 3-4 | 15 advanced queries |
| **Day 3** | Spreadsheets - Pivot Tables, VLOOKUP, Data Cleaning | 2-3 | 5 cleaned datasets |
| **Day 4** | Tableau - Visualizations, Dashboards, Calculated Fields | 3-4 | 3 dashboard projects |
| **Day 5** | Python for Analysis - Pandas, NumPy, Visualization | 3-4 | 2 analysis notebooks |
| **Day 6** | Statistics Refresher - A/B Testing, Hypothesis Testing | 2-3 | Cheat sheet + 10 problems |
| **Day 7** | **Week 1 Review & Integration Practice** | 3-4 | Timed mock technical assessment |

#### **Week 2: Interview Mastery (Days 8-14)**

| Day | Topic | Hours | Deliverable |
|-----|-------|-------|-------------|
| **Day 8** | Case Study Framework - Google's 6-step Process | 3-4 | 2 full case studies |
| **Day 9** | Product Sense & Metrics Design | 3-4 | 3 metric frameworks |
| **Day 10** | Behavioral & Leadership (Googleyness) | 2-3 | STAR story bank (8 stories) |
| **Day 11** | System Design for Analytics - Data Modeling | 3-4 | 2 ER diagrams + schema |
| **Day 12** | Communication & Presentation Skills | 2-3 | 2 recorded presentations |
| **Day 13** | **Full Mock Interview Loop** | 4-5 | Simulated 4-round interview |
| **Day 14** | **Final Review, Gaps, & Confidence Building** | 2-3 | Personalized cheat sheet |

---

### 🎓 Google Interview Format

| Round | Duration | Format | Focus |
|-------|----------|--------|-------|
| **Phone Screen** | 30-45 min | SQL + Behavioral | Basic competency |
| **Technical Screen** | 45-60 min | Live coding (SQL/Python) | Technical depth |
| **Case Study** | 45-60 min | Whiteboard/Discussion | Problem-solving, product sense |
| **Behavioral/Googliness** | 30-45 min | STAR format | Culture fit, leadership |
| **Hiring Committee** | Async | Review packet | Holistic evaluation |

---

### 📁 Course Materials Structure

```
data-analytics/
├── COURSE_OVERVIEW.md          # This file
├── GCP_DATA_ENGINEERING_COURSE/  # ⭐ The 34-chapter hands-on GCP course
├── GOOGLE_CLOUD_DATA_ANALYTICS_LEAD/
├── INTERVIEW_PREP/
├── WEEK_1_TECHNICAL/
├── WEEK_2_INTERVIEW/
├── CHEAT_SHEETS/
├── RESOURCES/
└── TRACKER/
```

---

### ⭐ GCP Data Engineering Course (the main build)

[`GCP_DATA_ENGINEERING_COURSE/`](GCP_DATA_ENGINEERING_COURSE/) is the
primary deliverable in this folder: **8 modules · 34 chapters · ~33,000
lines**, covering the Google Cloud platform from the mechanism up — IAM,
storage and databases, BigQuery, streaming, processing, orchestration,
governance and ML on GCP.

It ships with a **working project** that runs locally with no GCP
account, no credentials and no bill:

```bash
cd GCP_DATA_ENGINEERING_COURSE

python3 -m venv .venv && source .venv/bin/activate

# Generate the deterministic dataset
python resources/sample_data.py --output-dir ./sample_data

# Run the pipeline
python project/local_runner.py --run

# Run the tests and the course linter
python3 -m pytest project/tests/ -q
python resources/audit_course.py
```

The core modules import nothing from Google Cloud, so the whole platform
— the 34-service catalogue, the 23-role IAM policy engine, the cost
model and the pipeline — is modelled in pure Python and runs in under
half a second.

It also carries a bank of **128 interview questions** written the way a
senior engineer answers them: a direct answer, the mechanism, the
trade-off, and a production detail with numbers.

| Path | What it holds |
|------|---------------|
| [`GCP_DATA_ENGINEERING_COURSE/README.md`](GCP_DATA_ENGINEERING_COURSE/README.md) | Course front door, module map, how to run it |
| [`GCP_DATA_ENGINEERING_COURSE/chapters/`](GCP_DATA_ENGINEERING_COURSE/chapters/) | The 34 chapters |
| [`GCP_DATA_ENGINEERING_COURSE/project/`](GCP_DATA_ENGINEERING_COURSE/project/) | The runnable local simulation |
| [`GCP_DATA_ENGINEERING_COURSE/interview/`](GCP_DATA_ENGINEERING_COURSE/interview/) | 128 interview questions + a 14-day study plan |
| [`GCP_DATA_ENGINEERING_COURSE/resources/`](GCP_DATA_ENGINEERING_COURSE/resources/) | Setup, cheatsheet, glossary, FAQ, the linter |

The interview-prep directories above are the *analyst-side* package: SQL,
Python, statistics, case studies and behavioural rounds. The GCP Data
Engineering course is the *engineer-side* package. Together they cover
the whole interview loop.

---

### ✅ Success Criteria

By end of Week 1:
- [ ] Write complex SQL queries (CTEs, windows, subqueries) in <10 min
- [ ] Clean & analyze data in Sheets/Excel efficiently
- [ ] Build interactive Tableau dashboards from raw data
- [ ] Perform EDA in Python (pandas + visualization)
- [ ] Explain statistical concepts clearly

By end of Week 2:
- [ ] Solve case studies using Google's 6-step framework
- [ ] Design metrics for any product scenario
- [ ] Deliver 8+ polished STAR stories
- [ ] Design analytical data models
- [ ] Present findings to technical & non-technical audiences
- [ ] Pass full mock interview loop

---

### ⏰ Daily Time Commitment: 3-5 hours
### 🎯 Target: Ready for Google Data Analyst interviews in 14 days

---

*Generated for intensive prep. Adjust pace based on your background.*